"""Local filesystem storage implementation."""

from pathlib import Path
import aiofiles
import shutil
from typing import BinaryIO

from app.config import settings


class FileSystemStorage:
    """Local filesystem storage."""

    def __init__(self):
        self.storage_path = settings.storage_path
        self.temp_storage_path = settings.temp_storage_path

        # Ensure directories exist
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.temp_storage_path.mkdir(parents=True, exist_ok=True)

    def get_temp_path(self, suffix: str = "") -> Path:
        """Generate a temporary file path."""
        import uuid
        filename = f"tmp_{uuid.uuid4().hex}{suffix}"
        return self.temp_storage_path / filename

    def get_permanent_path(self, file_id: str, extension: str) -> Path:
        """Get permanent storage path for file."""
        filename = f"{file_id}{extension}"
        return self.storage_path / filename

    async def save_upload(self, file_content: BinaryIO, temp_path: Path) -> None:
        """Save uploaded file to temporary location."""
        async with aiofiles.open(temp_path, 'wb') as f:
            while chunk := file_content.read(8192):  # 8KB chunks
                await f.write(chunk)

    def move_to_permanent(self, temp_path: Path, permanent_path: Path) -> None:
        """Move file from temp to permanent storage."""
        shutil.move(str(temp_path), str(permanent_path))

    def cleanup_temp(self, temp_path: Path) -> None:
        """Remove temporary file."""
        if temp_path.exists():
            temp_path.unlink()

    def cleanup_permanent(self, permanent_path: Path) -> None:
        """Remove permanent file."""
        if permanent_path.exists():
            permanent_path.unlink()

    def file_exists(self, file_path: Path) -> bool:
        """Check if file exists."""
        return file_path.exists()

    def get_file_size(self, file_path: Path) -> int:
        """Get file size in bytes."""
        return file_path.stat().st_size


# Singleton instance
storage = FileSystemStorage()
