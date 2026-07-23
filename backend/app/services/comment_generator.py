"""Applies review findings as native Word comments.

Uses python-docx's own comment support (comments.xml part, relationships,
content-type registration, and w:commentRangeStart/End + commentReference
placement) rather than hand-rolling that plumbing — the result is a real,
Word-native comment.
"""

import logging

from docx import Document as DocxDocument

from app.models.review import ReviewFinding

logger = logging.getLogger(__name__)

_COMMENT_AUTHOR = "AI Contract Review"
_COMMENT_INITIALS = "AI"


def _format_comment_text(finding: ReviewFinding) -> str:
    lines = [
        f"Severity: {finding.severity.upper()}",
        f"Issue: {finding.issue_type}",
        f"Explanation: {finding.explanation}",
    ]
    if finding.suggested_text:
        lines.append(f"Suggested replacement: {finding.suggested_text}")
    return "\n".join(lines)


def apply_comments(docx_document: DocxDocument, runs: list, findings: list[ReviewFinding]) -> int:
    """Adds one Word comment per finding, anchored to the given (original,
    pre-modification) runs. Returns the number of comments actually created.

    `runs` must be a snapshot taken before any comment is added — re-reading
    `paragraph.runs` between calls would pick up the previous finding's own
    commentReference run and anchor the next comment to it too.
    """
    if not runs:
        logger.warning(
            "Skipping comments for an empty paragraph (finding_ids=%s)",
            [f.finding_id for f in findings],
        )
        return 0

    created = 0
    for finding in findings:
        docx_document.add_comment(
            runs=runs,
            text=_format_comment_text(finding),
            author=_COMMENT_AUTHOR,
            initials=_COMMENT_INITIALS,
        )
        created += 1
    return created
