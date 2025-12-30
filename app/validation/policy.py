"""Validation policies and rules."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Any

from app.models.file_asset import FileType


class Severity(str, Enum):
    """Rule severity levels."""
    ERROR = "ERROR"  # Blocks validation
    WARNING = "WARNING"  # Logged but doesn't block


@dataclass
class ValidationRule:
    """A single validation rule."""
    name: str
    severity: Severity
    description: str
    check: Callable[[dict], bool]  # Check function
    error_message: str
    expected: Any  # What should be true


class ValidationPolicy(ABC):
    """Abstract base class for validation policies."""

    @abstractmethod
    def get_rules(self, file_type: FileType) -> list[ValidationRule]:
        """Return rules for given file type."""
        pass


class StandardGenomicsPolicy(ValidationPolicy):
    """Phase 1: Hardcoded policy for all files."""

    def get_rules(self, file_type: FileType) -> list[ValidationRule]:
        """Get validation rules for file type."""
        if file_type == FileType.VCF:
            return self._vcf_rules()
        elif file_type == FileType.BAM:
            return self._bam_rules()
        else:
            return []

    def _vcf_rules(self) -> list[ValidationRule]:
        """VCF validation rules."""
        return [
            ValidationRule(
                name="has_header",
                severity=Severity.ERROR,
                description="VCF must have ##fileformat header",
                check=lambda m: m.get("format_version", "").startswith("VCFv4.") if m.get("format_version") else False,
                error_message="VCF file does not have a valid ##fileformat header",
                expected="##fileformat=VCFv4.x"
            ),
            ValidationRule(
                name="has_samples",
                severity=Severity.ERROR,
                description="VCF must have at least one sample",
                check=lambda m: m.get("sample_count", 0) > 0,
                error_message="VCF file must have at least one sample",
                expected=">= 1 sample"
            ),
            ValidationRule(
                name="has_index",
                severity=Severity.ERROR,
                description="VCF must have .tbi index",
                check=lambda m: m.get("has_index", False),
                error_message="VCF file must have a .tbi index file",
                expected=".tbi index file"
            ),
            ValidationRule(
                name="index_matches",
                severity=Severity.ERROR,
                description="Index contigs must match file contigs",
                check=self._check_vcf_index_matches,
                error_message="Index contigs do not match VCF file contigs",
                expected="matching contigs"
            ),
            ValidationRule(
                name="valid_version",
                severity=Severity.WARNING,
                description="VCFv4.3 is recommended",
                check=lambda m: m.get("format_version") == "VCFv4.3",
                error_message="VCFv4.3 is recommended for best compatibility",
                expected="VCFv4.3"
            ),
        ]

    def _bam_rules(self) -> list[ValidationRule]:
        """BAM validation rules."""
        return [
            ValidationRule(
                name="has_header",
                severity=Severity.ERROR,
                description="BAM must have valid header",
                check=lambda m: m.get("header") is not None and len(m.get("header", {})) > 0,
                error_message="BAM file does not have a valid header",
                expected="valid BAM header"
            ),
            ValidationRule(
                name="has_index",
                severity=Severity.ERROR,
                description="BAM must have .bai or .csi index",
                check=lambda m: m.get("has_index", False),
                error_message="BAM file must have a .bai or .csi index file",
                expected=".bai or .csi index"
            ),
            ValidationRule(
                name="index_matches",
                severity=Severity.ERROR,
                description="Index must be compatible with BAM",
                check=self._check_bam_index_matches,
                error_message="BAM index is not compatible with file",
                expected="compatible index"
            ),
        ]

    def _check_vcf_index_matches(self, metadata: dict) -> bool:
        """Check if VCF index matches file."""
        if not metadata.get("has_index"):
            return True  # N/A if no index

        file_contigs = set(metadata.get("contigs", []))
        index_contigs = set(metadata.get("index_contigs", []))

        # If index_contigs is None, we couldn't read the index
        if index_contigs is None:
            return False

        return file_contigs == index_contigs

    def _check_bam_index_matches(self, metadata: dict) -> bool:
        """Check if BAM index matches file."""
        if not metadata.get("has_index"):
            return True  # N/A if no index

        file_refs = set(metadata.get("references", []))
        index_refs = set(metadata.get("index_references", []))

        # If index_references is None, index is incompatible
        if index_refs is None:
            return False

        return file_refs == index_refs
