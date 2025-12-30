"""Pydantic schemas for file assets."""

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class FileState(str, Enum):
    """File lifecycle states."""
    UPLOADED = "UPLOADED"
    PREPARED = "PREPARED"
    VALIDATED = "VALIDATED"


class FileType(str, Enum):
    """Supported file types."""
    VCF = "VCF"
    BAM = "BAM"
    CRAM = "CRAM"


class FileUploadRequest(BaseModel):
    """Request schema for file upload."""
    file_type: FileType
    declared_metadata: Optional[dict[str, Any]] = None


class FileResponse(BaseModel):
    """Response schema for file operations."""
    id: str
    filename: str
    file_type: FileType
    state: FileState
    size_bytes: int
    checksum_sha256: str
    created_at: datetime
    updated_at: datetime
    declared_metadata: Optional[dict[str, Any]] = None
    observed_metadata: Optional[dict[str, Any]] = None
    validation_result: Optional[dict[str, Any]] = None
    validated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MetadataResponse(BaseModel):
    """Response schema for metadata endpoint."""
    file_id: str
    declared_metadata: Optional[dict[str, Any]] = None
    observed_metadata: Optional[dict[str, Any]] = None


class ValidationResult(BaseModel):
    """Validation result schema."""
    passed: bool
    passed_rules: list[str]
    failed_rules: list[dict[str, Any]]
    warnings: list[dict[str, Any]]


class Capabilities(BaseModel):
    """File capabilities schema."""
    can_query_regions: bool
    can_extract_samples: bool
    can_inspect_header: bool
    requires_index: bool
    supported_operations: list[str]
    limitations: list[str]
