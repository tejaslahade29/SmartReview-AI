"""Replaces company names with normalized roles before any text reaches Claude.

Detection is purely heuristic/regex — no model call happens here. Contracts
almost always self-define party roles near the top (e.g. `ABC Technologies
Pvt Ltd ("Supplier")`); we prefer that explicit definition over an assigned
generic label whenever one is present.
"""

import re
from dataclasses import dataclass, field

from app.models.document import DocumentParagraph

_SUFFIX = (
    r"(?:Pvt\.?\s*Ltd\.?|Private\s+Limited|Ltd\.?|Limited|L\.?L\.?C\.?|"
    r"Inc\.?|Incorporated|Corp\.?|Corporation|GmbH|AG|PLC|LLP|"
    r"Co\.?|Company|Group|Technologies|Solutions|Enterprises|Holdings)"
)
_COMPANY_NAME = rf"[A-Z][A-Za-z&.,]*(?:\s+(?:of|and|&)?\s*[A-Z][A-Za-z&.,]*){{0,5}}\s+{_SUFFIX}"

_COMPANY_NAME_RE = re.compile(_COMPANY_NAME)

_DEFINED_TERM_RE = re.compile(
    rf"(?P<name>{_COMPANY_NAME})\s*"
    r"\(\s*(?:the\s+)?(?:hereinafter,?\s*(?:referred\s+to\s+as\s*)?)?"
    r'["“](?:the\s+)?(?P<role>[A-Z][A-Za-z ]{1,40}?)["”]\s*\)'
)

_FALLBACK_ROLE_POOL = ["Client", "Vendor", "Customer", "Supplier", "Contractor", "Party A", "Party B"]


@dataclass
class PartyMappingEntry:
    original_name: str
    normalized_role: str


@dataclass
class PartyNormalizationResult:
    mapping: list[PartyMappingEntry] = field(default_factory=list)
    normalized_text_by_paragraph_id: dict[str, str] = field(default_factory=dict)


def _normalize_role_label(raw_role: str) -> str:
    return re.sub(r"\s+", " ", raw_role).strip().title()


def _build_name_to_role_map(full_text: str) -> dict[str, str]:
    name_to_role: dict[str, str] = {}
    used_roles: set[str] = set()

    for match in _DEFINED_TERM_RE.finditer(full_text):
        name = re.sub(r"\s+", " ", match.group("name")).strip()
        role = _normalize_role_label(match.group("role"))
        if name in name_to_role or role in used_roles:
            continue
        name_to_role[name] = role
        used_roles.add(role)

    candidate_counts: dict[str, int] = {}
    for match in _COMPANY_NAME_RE.finditer(full_text):
        name = re.sub(r"\s+", " ", match.group(0)).strip()
        candidate_counts[name] = candidate_counts.get(name, 0) + 1

    pool_index = 0
    for name, count in candidate_counts.items():
        if name in name_to_role or count < 2:
            continue
        while pool_index < len(_FALLBACK_ROLE_POOL) and _FALLBACK_ROLE_POOL[pool_index] in used_roles:
            pool_index += 1
        if pool_index >= len(_FALLBACK_ROLE_POOL):
            continue
        role = _FALLBACK_ROLE_POOL[pool_index]
        name_to_role[name] = role
        used_roles.add(role)
        pool_index += 1

    return name_to_role


def normalize_parties(paragraphs: list[DocumentParagraph]) -> PartyNormalizationResult:
    reviewable = [p for p in paragraphs if p.text and p.text.strip()]
    full_text = "\n".join(p.text for p in reviewable)

    name_to_role = _build_name_to_role_map(full_text)

    result = PartyNormalizationResult(
        mapping=[
            PartyMappingEntry(original_name=name, normalized_role=role)
            for name, role in name_to_role.items()
        ]
    )

    if not name_to_role:
        for paragraph in reviewable:
            result.normalized_text_by_paragraph_id[paragraph.id] = paragraph.text
        return result

    ordered_names = sorted(name_to_role.keys(), key=len, reverse=True)
    substitution_re = re.compile("|".join(re.escape(name) for name in ordered_names))

    def _replace(match: re.Match) -> str:
        return name_to_role[match.group(0)]

    for paragraph in reviewable:
        result.normalized_text_by_paragraph_id[paragraph.id] = substitution_re.sub(
            _replace, paragraph.text
        )

    return result
