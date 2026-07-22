"""Validates Claude's raw findings before anything gets persisted.

Never trust AI output directly — every finding is checked for required
fields, a real paragraph_id, a valid severity, and a sane confidence value.
Invalid or duplicate findings are dropped, not persisted.
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = ("finding_id", "paragraph_id", "issue_type", "severity", "explanation", "confidence")
_VALID_SEVERITIES = {"low", "medium", "high", "critical"}


@dataclass
class ValidatedFinding:
    finding_id: str
    paragraph_id: str
    issue_type: str
    severity: str
    explanation: str
    suggested_text: str | None
    confidence: float


def validate_findings(raw_findings: list[dict], valid_paragraph_ids: set[str]) -> list[ValidatedFinding]:
    validated: list[ValidatedFinding] = []
    seen_finding_ids: set[str] = set()

    for raw in raw_findings:
        if not isinstance(raw, dict):
            logger.warning("Dropping non-object finding: %r", raw)
            continue

        missing = [field for field in _REQUIRED_FIELDS if not raw.get(field)]
        if missing:
            logger.warning("Dropping finding missing fields %s: %r", missing, raw)
            continue

        finding_id = str(raw["finding_id"])
        if finding_id in seen_finding_ids:
            logger.warning("Dropping duplicate finding_id %s", finding_id)
            continue

        paragraph_id = str(raw["paragraph_id"])
        if paragraph_id not in valid_paragraph_ids:
            logger.warning(
                "Dropping finding %s: paragraph_id %s is not part of this document",
                finding_id,
                paragraph_id,
            )
            continue

        severity = str(raw["severity"]).lower()
        if severity not in _VALID_SEVERITIES:
            logger.warning("Dropping finding %s: invalid severity %r", finding_id, raw["severity"])
            continue

        try:
            confidence = float(raw["confidence"])
        except (TypeError, ValueError):
            logger.warning("Dropping finding %s: invalid confidence %r", finding_id, raw["confidence"])
            continue
        if not (0.0 <= confidence <= 1.0):
            logger.warning("Dropping finding %s: confidence out of range %r", finding_id, confidence)
            continue

        suggested_text = raw.get("suggested_text")
        suggested_text = str(suggested_text) if suggested_text else None

        seen_finding_ids.add(finding_id)
        validated.append(
            ValidatedFinding(
                finding_id=finding_id,
                paragraph_id=paragraph_id,
                issue_type=str(raw["issue_type"]),
                severity=severity,
                explanation=str(raw["explanation"]),
                suggested_text=suggested_text,
                confidence=confidence,
            )
        )

    return validated
