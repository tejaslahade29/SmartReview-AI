"""Applies severity-colored highlighting to a paragraph's runs.

Uses `w:shd` (run shading) rather than `w:highlight` — see
severity_styles.py for why. This is a real, Word-native run property, not
a simulated effect: it renders as a background fill and is editable via
Word's own shading controls.
"""

from docx.oxml.ns import qn
from docx.oxml.shared import OxmlElement

from app.services.severity_styles import SEVERITY_HIGHLIGHT_HEX


def _get_or_add_rpr(run_element):
    rpr = run_element.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        run_element.insert(0, rpr)
    return rpr


def apply_highlight(runs: list, severity: str) -> None:
    """`runs` must be the original content runs only — never re-derived
    from `paragraph.runs` after a comment reference run may have been
    inserted (see comment_generator.apply_comments)."""
    hex_color = SEVERITY_HIGHLIGHT_HEX.get(severity, SEVERITY_HIGHLIGHT_HEX["low"])

    for run in runs:
        rpr = _get_or_add_rpr(run._r)

        existing_shd = rpr.find(qn("w:shd"))
        if existing_shd is not None:
            rpr.remove(existing_shd)

        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:fill"), hex_color)
        rpr.append(shd)
