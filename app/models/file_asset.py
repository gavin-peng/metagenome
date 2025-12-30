"""FileAsset SQLAlchemy model."""

from sqlalchemy import Column, String, Integer, Enum as SQLEnum, JSON, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum

from app.db.database import Base


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


class FileAsset(Base):
    """File asset model with state machine and metadata."""

    __tablename__ = "file_assets"

    # Identity (checksum-based ID)
    id = Column(String, primary_key=True)  # sha256_{hash}
    filename = Column(String, nullable=False)
    file_type = Column(SQLEnum(FileType), nullable=False)

    # Content addressing
    checksum_sha256 = Column(String(64), nullable=False, unique=True, index=True)
    size_bytes = Column(Integer, nullable=False)

    # State machine
    state = Column(SQLEnum(FileState), nullable=False, default=FileState.UPLOADED)

    # Metadata
    declared_metadata = Column(JSON, nullable=True)  # User-provided
    observed_metadata = Column(JSON, nullable=True)  # Extracted from file

    # Validation
    validation_result = Column(JSON, nullable=True)
    validated_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FileAsset(id={self.id}, filename={self.filename}, state={self.state})>"


# Indexes for performance
Index("idx_file_type_state", FileAsset.file_type, FileAsset.state)
