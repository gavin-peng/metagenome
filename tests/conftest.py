"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import tempfile
import shutil

from app.main import app
from app.db.database import Base, get_db
from app.config import settings
from app.models.file_asset import FileAsset  # Import models to register with Base

# Test database (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db, temp_storage):
    """Create test client with test database and storage."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def temp_storage():
    """Create temporary storage directory."""
    temp_dir = Path(tempfile.mkdtemp())
    original_storage = settings.storage_path
    original_temp = settings.temp_storage_path

    settings.storage_path = temp_dir / "storage"
    settings.temp_storage_path = temp_dir / "temp"
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    settings.temp_storage_path.mkdir(parents=True, exist_ok=True)

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)
    settings.storage_path = original_storage
    settings.temp_storage_path = original_temp


@pytest.fixture
def sample_vcf_content():
    """Sample VCF file content."""
    return b"""##fileformat=VCFv4.2
##contig=<ID=chr1,length=248956422>
##contig=<ID=chr2,length=242193529>
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE1
chr1\t1000\t.\tA\tG\t30\tPASS\t.\tGT\t0/1
"""
