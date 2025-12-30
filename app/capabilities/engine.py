"""Capabilities engine for computing file capabilities."""

from app.models.file_asset import FileAsset, FileState, FileType
from app.schemas.file_asset import Capabilities


class CapabilitiesEngine:
    """Computes file capabilities dynamically."""

    @staticmethod
    def compute_capabilities(file: FileAsset) -> Capabilities:
        """Compute capabilities based on file metadata."""

        metadata = file.observed_metadata or {}

        # Extract key metadata
        has_index = metadata.get("has_index", False)
        sample_count = metadata.get("sample_count", 0)
        has_header = file.state in [FileState.PREPARED, FileState.VALIDATED]
        file_type = file.file_type

        # Base capabilities
        can_query_regions = has_index
        can_extract_samples = sample_count > 0 and file_type == FileType.VCF
        can_inspect_header = has_header

        # Dynamic operations
        operations = []
        if can_query_regions:
            operations.append("region_query")
        if can_extract_samples:
            operations.append("sample_extraction")
        if can_inspect_header:
            operations.append("header_inspection")

        # Limitations
        limitations = []
        if not has_index:
            limitations.append("no_region_queries: Index file required")
        if file_type == FileType.VCF and sample_count == 0:
            limitations.append("no_sample_extraction: File has no samples")
        if file_type != FileType.VCF:
            limitations.append("no_sample_extraction: Only VCF files support sample extraction")
        if not has_header:
            limitations.append("no_header_inspection: File not prepared")

        return Capabilities(
            can_query_regions=can_query_regions,
            can_extract_samples=can_extract_samples,
            can_inspect_header=can_inspect_header,
            requires_index=True,
            supported_operations=operations,
            limitations=[l for l in limitations if l]  # Remove empty strings
        )
