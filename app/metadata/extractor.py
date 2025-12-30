"""Metadata extraction dispatcher."""

from pathlib import Path
from typing import Any
import asyncio

from app.models.file_asset import FileType
from app.metadata.vcf import extract_vcf_metadata
from app.metadata.bam import extract_bam_metadata
from app.errors.exceptions import SemanticError


async def extract_metadata(file_path: Path, file_type: FileType) -> dict[str, Any]:
    """Extract metadata from genomic file headers.

    Runs in thread pool to avoid blocking event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # Default executor
        _extract_metadata_sync,
        file_path,
        file_type
    )


def _extract_metadata_sync(file_path: Path, file_type: FileType) -> dict[str, Any]:
    """Synchronous metadata extraction."""
    if file_type == FileType.VCF:
        return extract_vcf_metadata(file_path)
    elif file_type == FileType.BAM:
        return extract_bam_metadata(file_path)
    else:
        raise SemanticError(
            f"Unsupported file type for metadata extraction: {file_type}",
            file_type=file_type.value
        )
