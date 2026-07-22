"""Deterministic agreement-type classification.

Runs before Claude is ever called — it's a cheap keyword heuristic, not a
model call, so ClaudeService remains the only component that talks to
Anthropic.
"""

import re

from app.models.document import DocumentParagraph

# Ordered so a more specific phrase (e.g. "master service agreement") is
# checked before a more generic one that could also match it.
_HEADING_PATTERNS: list[tuple[str, str]] = [
    ("NDA", r"non-?disclosure agreement|confidentiality agreement"),
    ("DPA", r"data processing agreement"),
    ("MSA", r"master servic(?:e|es) agreement"),
    ("SOW", r"statement of work|scope of work"),
    ("Employment Agreement", r"employment agreement"),
    ("Service Agreement", r"servic(?:e|es) agreement"),
]

_KEYWORD_SCORES: dict[str, list[str]] = {
    "NDA": ["non-disclosure", "nondisclosure", "confidential information", "disclosing party", "receiving party"],
    "MSA": ["master service agreement", "master services agreement", "statement of work"],
    "DPA": ["data processing agreement", "data controller", "data processor", "gdpr", "personal data"],
    "SOW": ["statement of work", "scope of work", "deliverables", "milestones"],
    "Service Agreement": ["service agreement", "services agreement", "scope of services"],
    "Employment Agreement": ["employment agreement", "employee", "employer", "at-will employment", "job title"],
}


def _first_heading_text(paragraphs: list[DocumentParagraph]) -> str | None:
    for paragraph in paragraphs:
        if paragraph.location == "body" and paragraph.paragraph_type == "heading":
            return paragraph.text
    return None


def detect_agreement_type(paragraphs: list[DocumentParagraph]) -> str:
    heading = _first_heading_text(paragraphs)
    if heading:
        lowered_heading = heading.lower()
        for agreement_type, pattern in _HEADING_PATTERNS:
            if re.search(pattern, lowered_heading):
                return agreement_type

    full_text = " ".join(p.text for p in paragraphs if p.location == "body").lower()
    if not full_text.strip():
        return "Unknown"

    scores: dict[str, int] = {}
    for agreement_type, keywords in _KEYWORD_SCORES.items():
        score = sum(full_text.count(keyword) for keyword in keywords)
        if score > 0:
            scores[agreement_type] = score

    if not scores:
        return "Unknown"

    return max(scores, key=lambda k: scores[k])
