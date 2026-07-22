"""Builds the Claude review prompt centrally.

The Review Engine never concatenates prompt text itself — it passes
agreement type + normalized clauses here and gets back a finished prompt
plus the JSON schema Claude's response must satisfy.
"""

from dataclasses import dataclass

_DEFAULT_RULES = [
    "Flag one-sided obligations, unusual liability exposure, and terms that deviate from standard commercial practice.",
    "Do not flag boilerplate or standard clauses that carry no real risk.",
]

_REVIEW_RULES: dict[str, list[str]] = {
    "NDA": [
        "Check whether the definition of confidential information is overly broad or one-sided.",
        "Check the duration of confidentiality obligations for reasonableness.",
        "Check for a clause requiring return or destruction of confidential information.",
        "Check whether obligations are mutual or fall on only one party without justification.",
    ],
    "MSA": [
        "Check limitation-of-liability caps and whether they are mutual.",
        "Check indemnification scope for one-sidedness.",
        "Check termination rights and notice periods for both parties.",
        "Check intellectual property ownership and assignment terms.",
        "Check payment terms and late-payment consequences.",
    ],
    "DPA": [
        "Check that data processor obligations align with data protection law (e.g. GDPR Article 28).",
        "Check for breach-notification timelines.",
        "Check sub-processor authorization requirements.",
        "Check data deletion/return obligations at contract end.",
    ],
    "SOW": [
        "Check that deliverables and acceptance criteria are clearly defined.",
        "Check milestone and payment schedule alignment.",
        "Check change-order / scope-change procedures.",
    ],
    "Service Agreement": [
        "Check scope of services for ambiguity.",
        "Check service levels and remedies for missed levels.",
        "Check termination and renewal terms.",
    ],
    "Employment Agreement": [
        "Check non-compete and non-solicitation scope and duration for enforceability risk.",
        "Check termination and severance terms.",
        "Check IP assignment and confidentiality obligations.",
    ],
    "Unknown": [],
}

_SYSTEM_PROMPT = (
    "You are a contract review assistant supporting a company's legal team. "
    "You review agreements the company has received from a counterparty and identify "
    "clauses that are unfavorable, risky, or non-standard from the company's perspective. "
    "You do not draft new agreements and you do not rewrite the whole document — you only "
    "produce structured findings about specific clauses.\n\n"
    "Party names in the text below have already been replaced with normalized roles "
    "(e.g. Client, Vendor, Supplier). Reason about obligations and risk allocation between "
    "these roles, not about the identity of any specific company.\n\n"
    "Only flag genuine issues. Do not invent risks in clauses that are standard or balanced. "
    "Each finding must reference the exact paragraph_id of the clause it concerns — never "
    "invent a paragraph_id that wasn't given to you."
)

FINDINGS_JSON_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "finding_id": {"type": "string"},
                    "paragraph_id": {"type": "string"},
                    "issue_type": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "explanation": {"type": "string"},
                    "suggested_text": {"type": ["string", "null"]},
                    "confidence": {"type": "number"},
                },
                "required": [
                    "finding_id",
                    "paragraph_id",
                    "issue_type",
                    "severity",
                    "explanation",
                    "suggested_text",
                    "confidence",
                ],
                "additionalProperties": False,
            },
        },
    },
    "required": ["findings"],
    "additionalProperties": False,
}


@dataclass
class PromptBundle:
    system: str
    user_message: str
    json_schema: dict


def build_review_prompt(
    agreement_type: str,
    normalized_clauses: list[tuple[str, str]],
) -> PromptBundle:
    """normalized_clauses is a list of (paragraph_id, normalized_text) pairs."""

    rules = _REVIEW_RULES.get(agreement_type, []) + _DEFAULT_RULES
    rules_text = "\n".join(f"- {rule}" for rule in rules)

    clause_lines = "\n".join(
        f"[paragraph_id: {paragraph_id}] {text}"
        for paragraph_id, text in normalized_clauses
        if text.strip()
    )

    user_message = (
        f"Agreement type: {agreement_type}\n\n"
        f"Review guidance for this agreement type:\n{rules_text}\n\n"
        "Review the following clauses. Each is tagged with its paragraph_id — use that exact "
        "id in any finding you return, and only return findings for clauses listed below.\n\n"
        f"{clause_lines}"
    )

    return PromptBundle(system=_SYSTEM_PROMPT, user_message=user_message, json_schema=FINDINGS_JSON_SCHEMA)
