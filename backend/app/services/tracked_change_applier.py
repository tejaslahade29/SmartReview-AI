"""Converts a paragraph's text into a real tracked-change replacement.

Wraps the existing runs in `w:del` (with `w:t` renamed to `w:delText`, per
spec — deleted text cannot use `w:t`) and inserts the suggested text as a
`w:ins`. These are the actual OOXML revision elements Word uses for
Track Changes — opening the result in Word and clicking Accept/Reject
behaves exactly as if a person had made the edit, because from Word's
perspective, that's indistinguishable from what happened here.
"""

import copy
import datetime

from docx.oxml.ns import qn
from docx.oxml.shared import OxmlElement
from docx.text.paragraph import Paragraph as DocxParagraph

_AUTHOR = "AI Contract Review"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_insertion_anchor(last_run_element):
    """Walks past any comment-range-end / comment-reference markers that
    immediately follow the last original run, so the tracked insertion
    stays inside the same comment's visual anchor range.
    """
    anchor = last_run_element
    next_el = anchor.getnext()
    while next_el is not None and (
        next_el.tag == qn("w:commentRangeEnd")
        or (next_el.tag == qn("w:r") and next_el.find(qn("w:commentReference")) is not None)
    ):
        anchor = next_el
        next_el = anchor.getnext()
    return anchor


def apply_tracked_replacement(
    paragraph: DocxParagraph, runs: list, suggested_text: str, next_revision_id: int
) -> int:
    """Returns the next free revision id for the caller to continue from.

    `runs` must be the original content runs only — never re-derived from
    `paragraph.runs` after a comment reference run may have been inserted
    (see comment_generator.apply_comments); that marker run must never be
    wrapped in a tracked deletion.
    """
    original_runs = list(runs)
    if not original_runs:
        return next_revision_id

    p = paragraph._p
    anchor = _find_insertion_anchor(original_runs[-1]._r)
    insertion_index = list(p).index(anchor) + 1
    first_rpr = original_runs[0]._r.find(qn("w:rPr"))

    revision_id = next_revision_id
    now = _now_iso()

    for run in original_runs:
        r_el = run._r
        parent = r_el.getparent()
        position = list(parent).index(r_el)

        del_el = OxmlElement("w:del")
        del_el.set(qn("w:id"), str(revision_id))
        del_el.set(qn("w:author"), _AUTHOR)
        del_el.set(qn("w:date"), now)
        revision_id += 1

        parent.remove(r_el)
        for t_el in r_el.findall(qn("w:t")):
            t_el.tag = qn("w:delText")
            t_el.set(qn("xml:space"), "preserve")
        del_el.append(r_el)
        parent.insert(position, del_el)

    ins_el = OxmlElement("w:ins")
    ins_el.set(qn("w:id"), str(revision_id))
    ins_el.set(qn("w:author"), _AUTHOR)
    ins_el.set(qn("w:date"), now)
    revision_id += 1

    new_run = OxmlElement("w:r")
    if first_rpr is not None:
        new_run.append(copy.deepcopy(first_rpr))
    t_el = OxmlElement("w:t")
    t_el.set(qn("xml:space"), "preserve")
    t_el.text = suggested_text
    new_run.append(t_el)
    ins_el.append(new_run)

    p.insert(insertion_index, ins_el)

    return revision_id


def next_free_revision_id(docx_document) -> int:
    """Scans the whole document body for existing w:ins/w:del ids so newly
    generated ids never collide with tracked changes already present.
    """
    max_id = 0
    body = docx_document.element.body
    for tag in ("w:ins", "w:del"):
        for element in body.iter(qn(tag)):
            value = element.get(qn("w:id"))
            if value and value.lstrip("-").isdigit():
                max_id = max(max_id, int(value))
    return max_id + 1
