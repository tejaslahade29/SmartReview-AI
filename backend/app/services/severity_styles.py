"""Centralized severity -> visual style mapping.

OOXML's `w:highlight` element only supports a fixed legacy color
enumeration (black, blue, cyan, ..., red, yellow — no orange), so
highlighting is implemented with `w:shd` (run shading) instead, which
accepts arbitrary hex fill colors while still rendering as a native,
Word-editable background — not a simulated effect.
"""

SEVERITY_HIGHLIGHT_HEX = {
    "critical": "FF0000",
    "high": "FFA500",
    "medium": "FFFF00",
    "low": "9CC3E5",
}

_SEVERITY_ORDER = ["low", "medium", "high", "critical"]


def highest_severity(severities: list[str]) -> str:
    return max(severities, key=_SEVERITY_ORDER.index)
