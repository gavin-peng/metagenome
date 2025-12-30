"""API endpoints for file asset management."""

from fastapi import APIRouter, UploadFile, File, Form, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pathlib import Path
import hashlib
import asyncio
import json
from typing import Optional
from datetime import datetime

from app.db.database import get_db
from app.models.file_asset import FileAsset, FileState, FileType
from app.schemas.file_asset import FileResponse, MetadataResponse
from app.errors.exceptions import (
    StateConflictError,
    SemanticError,
    ChecksumMismatchError,
    FileNotFoundError,
    RequestTimeoutError,
    ValidationFailedError,
)
from app.storage.filesystem import storage
from app.metadata.extractor import extract_metadata
from app.validation.policy import StandardGenomicsPolicy
from app.validation.engine import ValidationEngine
from app.capabilities.engine import CapabilitiesEngine
from app.config import settings

router = APIRouter()


# Helper functions

def get_file_or_404(db: Session, file_id: str) -> FileAsset:
    """Get file by ID or raise 404."""
    file = db.query(FileAsset).filter(FileAsset.id == file_id).first()
    if not file:
        raise FileNotFoundError(file_id)
    return file


async def compute_checksum_and_save(
    file: UploadFile,
    temp_path: Path
) -> tuple[str, int]:
    """Compute SHA-256 checksum while saving file."""
    hasher = hashlib.sha256()
    size = 0

    with open(temp_path, 'wb') as f:
        while chunk := await file.read(8192):  # 8KB chunks
            hasher.update(chunk)
            f.write(chunk)
            size += len(chunk)

    checksum = hasher.hexdigest()
    return checksum, size


# API Endpoints

@router.post("/files", status_code=201, response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_type: str = Form(...),
    declared_metadata: Optional[str] = Form(None),
    x_checksum_sha256: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Upload and register a genomic file.

    Returns 201 Created for new files, 200 OK for duplicate uploads (idempotent).
    """
    # Validate file_type
    try:
        file_type_enum = FileType(file_type)
    except ValueError:
        raise SemanticError(
            f"Invalid file type: {file_type}",
            field="file_type",
            expected="VCF | BAM | CRAM",
            received=file_type
        )

    # Parse declared_metadata
    declared_meta = None
    if declared_metadata:
        try:
            declared_meta = json.loads(declared_metadata)
        except json.JSONDecodeError as e:
            raise SemanticError(
                "Invalid JSON in declared_metadata",
                error=str(e)
            )

    # Get file extension
    file_extension = Path(file.filename).suffix if file.filename else ""

    # Save to temporary location and compute checksum
    temp_path = storage.get_temp_path(file_extension)

    try:
        checksum, size = await compute_checksum_and_save(file, temp_path)

        # Validate client checksum if provided
        if x_checksum_sha256 and x_checksum_sha256 != checksum:
            storage.cleanup_temp(temp_path)
            raise ChecksumMismatchError(x_checksum_sha256, checksum)

        file_id = f"sha256_{checksum}"

        # Check if file already exists (idempotency)
        existing = db.query(FileAsset).filter(
            FileAsset.checksum_sha256 == checksum
        ).first()

        if existing:
            storage.cleanup_temp(temp_path)
            return FileResponse.model_validate(existing)

        # Move to permanent storage
        permanent_path = storage.get_permanent_path(file_id, file_extension)
        storage.move_to_permanent(temp_path, permanent_path)

        # Create database record
        file_asset = FileAsset(
            id=file_id,
            filename=file.filename or "unknown",
            file_type=file_type_enum,
            checksum_sha256=checksum,
            size_bytes=size,
            declared_metadata=declared_meta,
            state=FileState.UPLOADED
        )

        try:
            db.add(file_asset)
            db.commit()
            db.refresh(file_asset)
            return FileResponse.model_validate(file_asset)

        except IntegrityError:
            # Race condition: another request uploaded same file
            db.rollback()
            storage.cleanup_permanent(permanent_path)
            existing = db.query(FileAsset).filter(
                FileAsset.checksum_sha256 == checksum
            ).first()
            return FileResponse.model_validate(existing)

    except Exception as e:
        storage.cleanup_temp(temp_path)
        raise


@router.post("/files/{file_id}/prepare", response_model=FileResponse)
async def prepare_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Extract metadata from file headers (synchronous, 5s timeout)."""

    file = get_file_or_404(db, file_id)

    # Validate state
    if file.state != FileState.UPLOADED:
        raise StateConflictError(
            f"Cannot prepare file in state {file.state.value}",
            file_id=file_id,
            current_state=file.state.value,
            expected_state=FileState.UPLOADED.value,
            suggestion=f"File is already in {file.state.value} state"
        )

    # Get file path
    file_extension = Path(file.filename).suffix
    file_path = storage.get_permanent_path(file_id, file_extension)

    if not storage.file_exists(file_path):
        raise SemanticError(
            "File not found in storage",
            file_id=file_id,
            path=str(file_path)
        )

    try:
        # Run extraction with timeout
        async with asyncio.timeout(settings.prepare_timeout_seconds):
            metadata = await extract_metadata(file_path, file.file_type)

        # Update database
        file.observed_metadata = metadata
        file.state = FileState.PREPARED
        db.commit()
        db.refresh(file)

        return FileResponse.model_validate(file)

    except asyncio.TimeoutError:
        raise RequestTimeoutError(
            f"Metadata extraction exceeded {settings.prepare_timeout_seconds} second timeout",
            operation="prepare",
            file_id=file_id,
            timeout_seconds=settings.prepare_timeout_seconds,
            suggestion="File may be corrupted or on slow storage"
        )


@router.post("/files/{file_id}/validate", response_model=FileResponse)
async def validate_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Validate file against policy rules."""

    file = get_file_or_404(db, file_id)

    # Check state
    if file.state != FileState.PREPARED:
        raise StateConflictError(
            f"Cannot validate file in state {file.state.value}",
            file_id=file_id,
            current_state=file.state.value,
            expected_state=FileState.PREPARED.value,
            suggestion="Run POST /files/{id}/prepare first" if file.state == FileState.UPLOADED else f"File is already {file.state.value}"
        )

    # Run validation
    policy = StandardGenomicsPolicy()
    engine = ValidationEngine(policy)

    result = await engine.validate_file(file)

    # Update database
    file.validation_result = {
        "passed": result.passed,
        "passed_rules": result.passed_rules,
        "failed_rules": result.failed_rules,
        "warnings": result.warnings
    }

    if result.passed:
        file.state = FileState.VALIDATED
        file.validated_at = datetime.utcnow()

    db.commit()
    db.refresh(file)

    # Return success or failure
    if result.passed:
        return FileResponse.model_validate(file)
    else:
        raise ValidationFailedError(
            "File validation failed",
            file_id=file_id,
            failed_rules=result.failed_rules,
            passed_rules=result.passed_rules,
            warnings=result.warnings
        )


@router.get("/files/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Get file summary."""
    file = get_file_or_404(db, file_id)
    return FileResponse.model_validate(file)


@router.get("/files/{file_id}/metadata", response_model=MetadataResponse)
async def get_metadata(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Get file metadata (declared + observed)."""
    file = get_file_or_404(db, file_id)

    return MetadataResponse(
        file_id=file.id,
        declared_metadata=file.declared_metadata,
        observed_metadata=file.observed_metadata
    )


@router.get("/files/{file_id}/capabilities")
async def get_capabilities(
    file_id: str,
    db: Session = Depends(get_db)
):
    """Get file capabilities."""
    file = get_file_or_404(db, file_id)

    # Compute capabilities
    capabilities = CapabilitiesEngine.compute_capabilities(file)

    return capabilities.model_dump()
