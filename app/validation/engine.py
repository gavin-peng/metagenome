"""Validation engine for checking files against policies."""

from typing import Any

from app.models.file_asset import FileAsset
from app.validation.policy import ValidationPolicy, Severity
from app.schemas.file_asset import ValidationResult
from app.errors.exceptions import SemanticError


class ValidationEngine:
    """Validates files against policies."""

    def __init__(self, policy: ValidationPolicy):
        self.policy = policy

    async def validate_file(self, file: FileAsset) -> ValidationResult:
        """Validate file against policy rules."""

        # Get metadata
        metadata = file.observed_metadata
        if not metadata:
            raise SemanticError(
                "Cannot validate file without metadata",
                file_id=file.id,
                suggestion="Run POST /files/{id}/prepare first"
            )

        # Get rules for file type
        rules = self.policy.get_rules(file.file_type)

        passed_rules = []
        failed_rules = []
        warnings = []

        # Check each rule
        for rule in rules:
            try:
                passed = rule.check(metadata)
            except Exception as e:
                # If rule check fails, treat as validation failure
                passed = False

            if passed:
                passed_rules.append(rule.name)
            else:
                failure = {
                    "rule": rule.name,
                    "severity": rule.severity.value,
                    "message": rule.error_message,
                    "expected": rule.expected,
                    "found": self._get_found_value(metadata, rule)
                }

                if rule.severity == Severity.ERROR:
                    failed_rules.append(failure)
                else:
                    warnings.append(failure)

        # Validation passes if no ERROR-level failures
        validation_passed = len(failed_rules) == 0

        return ValidationResult(
            passed=validation_passed,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings
        )

    def _get_found_value(self, metadata: dict, rule) -> Any:
        """Extract the value that was checked."""
        if rule.name == "has_header":
            return metadata.get("format_version") or metadata.get("header")
        elif rule.name == "has_samples":
            return metadata.get("sample_count", 0)
        elif rule.name == "has_index":
            return "index found" if metadata.get("has_index") else "index not found"
        elif rule.name == "index_matches":
            if not metadata.get("has_index"):
                return "N/A"
            file_items = metadata.get("contigs") or metadata.get("references")
            index_items = metadata.get("index_contigs") or metadata.get("index_references")
            return {"file": file_items, "index": index_items}
        elif rule.name == "valid_version":
            return metadata.get("format_version")
        else:
            return None
