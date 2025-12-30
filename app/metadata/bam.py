"""BAM metadata extraction using pysam."""

from pathlib import Path
from typing import Any
import pysam

from app.errors.exceptions import SemanticError


def extract_bam_metadata(file_path: Path) -> dict[str, Any]:
    """Extract BAM header information and check for index."""
    try:
        # Open BAM file
        bam = pysam.AlignmentFile(str(file_path), "rb")

        # Extract header information
        header = dict(bam.header.to_dict()) if bam.header else None
        references = list(bam.references) if bam.references else []
        read_groups = []
        if header and 'RG' in header:
            read_groups = [rg.get('ID') for rg in header['RG']]

        # Check for BAI index
        bai_path = Path(f"{file_path}.bai")
        has_bai = bai_path.exists()

        # Check for CSI index (alternative)
        csi_path = Path(f"{file_path}.csi")
        has_csi = csi_path.exists()

        has_index = has_bai or has_csi
        index_type = "bai" if has_bai else ("csi" if has_csi else None)

        # If index exists, verify it's compatible
        index_references = None
        if has_index:
            try:
                # Check if index works
                if bam.check_index():
                    index_references = references  # BAM and index must have same refs
            except Exception:
                has_index = False
                index_type = None

        metadata = {
            "header": header,
            "references": references,
            "reference_count": len(references),
            "read_groups": read_groups,
            "has_index": has_index,
            "index_type": index_type,
            "index_references": index_references
        }

        bam.close()
        return metadata

    except Exception as e:
        raise SemanticError(
            f"Failed to extract BAM metadata: {str(e)}",
            file_path=str(file_path),
            error=str(e),
            suggestion="Ensure file is a valid BAM format and not corrupted"
        )
