"""Integration tests for file upload endpoint."""

import pytest
from io import BytesIO


def test_upload_file_success(client):
    """Test successful file upload."""
    file_content = b"test file content"
    files = {"file": ("test.vcf.gz", BytesIO(file_content), "application/gzip")}
    data = {"file_type": "VCF"}

    response = client.post("/files", files=files, data=data)

    assert response.status_code == 201
    result = response.json()
    assert result["filename"] == "test.vcf.gz"
    assert result["file_type"] == "VCF"
    assert result["state"] == "UPLOADED"
    assert "sha256_" in result["id"]


def test_upload_duplicate_file(client):
    """Test idempotent upload (duplicate file)."""
    file_content = b"duplicate content"
    files = {"file": ("test.vcf.gz", BytesIO(file_content), "application/gzip")}
    data = {"file_type": "VCF"}

    # First upload
    response1 = client.post("/files", files=files, data=data)
    assert response1.status_code == 201
    file_id = response1.json()["id"]

    # Second upload (same content)
    files2 = {"file": ("test.vcf.gz", BytesIO(file_content), "application/gzip")}
    response2 = client.post("/files", files=files2, data=data)

    assert response2.status_code == 200  # OK, not Created
    assert response2.json()["id"] == file_id  # Same ID


def test_upload_invalid_file_type(client):
    """Test upload with invalid file type."""
    files = {"file": ("test.txt", BytesIO(b"content"), "text/plain")}
    data = {"file_type": "INVALID"}

    response = client.post("/files", files=files, data=data)

    assert response.status_code == 422
    assert "SEMANTIC_ERROR" in response.json()["error"]["code"]


def test_get_file_success(client):
    """Test GET /files/{id} endpoint."""
    # Upload file first
    files = {"file": ("test.vcf.gz", BytesIO(b"content"), "application/gzip")}
    data = {"file_type": "VCF"}
    upload_response = client.post("/files", files=files, data=data)
    file_id = upload_response.json()["id"]

    # Get file
    response = client.get(f"/files/{file_id}")

    assert response.status_code == 200
    result = response.json()
    assert result["id"] == file_id


def test_get_file_not_found(client):
    """Test GET /files/{id} with non-existent file."""
    response = client.get("/files/sha256_nonexistent")

    assert response.status_code == 404
    assert "FILE_NOT_FOUND" in response.json()["error"]["code"]
