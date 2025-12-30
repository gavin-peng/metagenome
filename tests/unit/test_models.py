"""Unit tests for FileAsset model."""

import pytest
from datetime import datetime

from app.models.file_asset import FileAsset, FileState, FileType


def test_file_asset_creation(db):
    """Test creating a FileAsset."""
    file = FileAsset(
        id="sha256_test123",
        filename="test.vcf.gz",
        file_type=FileType.VCF,
        checksum_sha256="test123",
        size_bytes=1024,
        state=FileState.UPLOADED
    )

    db.add(file)
    db.commit()
    db.refresh(file)

    assert file.id == "sha256_test123"
    assert file.state == FileState.UPLOADED
    assert file.created_at is not None


def test_file_asset_state_transition(db):
    """Test state machine transitions."""
    file = FileAsset(
        id="sha256_test456",
        filename="test.bam",
        file_type=FileType.BAM,
        checksum_sha256="test456",
        size_bytes=2048,
        state=FileState.UPLOADED
    )

    db.add(file)
    db.commit()

    # Transition to PREPARED
    file.state = FileState.PREPARED
    file.observed_metadata = {"header": "test"}
    db.commit()

    assert file.state == FileState.PREPARED
    assert file.observed_metadata == {"header": "test"}

    # Transition to VALIDATED
    file.state = FileState.VALIDATED
    file.validated_at = datetime.utcnow()
    db.commit()

    assert file.state == FileState.VALIDATED
    assert file.validated_at is not None


def test_checksum_uniqueness(db):
    """Test checksum unique constraint."""
    file1 = FileAsset(
        id="sha256_unique1",
        filename="file1.vcf.gz",
        file_type=FileType.VCF,
        checksum_sha256="duplicate_checksum",
        size_bytes=1024,
        state=FileState.UPLOADED
    )

    db.add(file1)
    db.commit()

    # Try to add duplicate checksum
    file2 = FileAsset(
        id="sha256_unique2",
        filename="file2.vcf.gz",
        file_type=FileType.VCF,
        checksum_sha256="duplicate_checksum",  # Same checksum
        size_bytes=2048,
        state=FileState.UPLOADED
    )

    db.add(file2)

    with pytest.raises(Exception):  # IntegrityError
        db.commit()
