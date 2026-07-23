"""Maps a stable paragraph_id back to the live lxml element in a freshly
opened copy of the ORIGINAL document.

Never searches by text. The parser's traversal order is deterministic, so
re-parsing the exact same original bytes reproduces the exact same sequence
of paragraphs it produced at upload time — DocumentParagraph.sequence_index
is that sequence's position, and it's the only thing we key off.
"""

from docx import Document as DocxDocument
from docx.text.paragraph import Paragraph as DocxParagraph

from app.core.exceptions import ValidationFailedError
from app.models.document import DocumentParagraph
from app.services.document_parser import open_and_parse


def locate_paragraphs(
    original_bytes: bytes, db_paragraphs: list[DocumentParagraph]
) -> tuple[DocxDocument, dict[str, DocxParagraph]]:
    """Returns the freshly opened DocxDocument plus a paragraph_id -> live
    Paragraph map. The caller must mutate and save this same DocxDocument —
    the map's elements belong to its tree, not to any other copy.
    """

    docx_document, fresh = open_and_parse(original_bytes)

    if len(fresh.paragraphs) != len(db_paragraphs):
        raise ValidationFailedError(
            "The original document no longer matches its parsed structure "
            "(paragraph count mismatch) — cannot safely locate paragraphs."
        )

    element_by_id: dict[str, DocxParagraph] = {}
    for db_paragraph in db_paragraphs:
        parsed_paragraph = fresh.paragraphs[db_paragraph.sequence_index]
        if parsed_paragraph.source is None:
            raise ValidationFailedError(
                f"Could not locate a live element for paragraph '{db_paragraph.id}'."
            )
        element_by_id[db_paragraph.id] = parsed_paragraph.source

    return docx_document, element_by_id
