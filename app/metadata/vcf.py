"""VCF metadata extraction using pysam."""

from pathlib import Path
from typing import Any
import pysam

from app.errors.exceptions import SemanticError


def extract_vcf_metadata(file_path: Path) -> dict[str, Any]:
    """Extract VCF header information and check for index."""
    try:
        # Open VCF file
        vcf = pysam.VariantFile(str(file_path))

        # Extract header information
        format_version = vcf.header.version if hasattr(vcf.header, 'version') else None
        samples = list(vcf.header.samples)
        sample_count = len(samples)
        contigs = [str(contig) for contig in vcf.header.contigs.keys()]

        # Check for tabix index (.tbi)
        index_path = Path(f"{file_path}.tbi")
        has_index = index_path.exists()

        # If index exists, verify it matches
        index_contigs = None
        if has_index:
            try:
                # Try to use the index
                tbx = pysam.TabixFile(str(file_path))
                index_contigs = list(tbx.contigs)
                tbx.close()
            except Exception:
                # Index may be corrupted or incompatible
                has_index = False

        metadata = {
            "format_version": format_version,
            "sample_count": sample_count,
            "samples": samples,
            "contigs": contigs,
            "has_index": has_index,
            "index_type": "tbi" if has_index else None,
            "index_contigs": index_contigs
        }

        vcf.close()
        return metadata

    except Exception as e:
        raise SemanticError(
            f"Failed to extract VCF metadata: {str(e)}",
            file_path=str(file_path),
            error=str(e),
            suggestion="Ensure file is a valid VCF/BCF format and not corrupted"
        )
