"""The ONLY component allowed to talk to the Anthropic SDK.

Every other module that needs Claude's reasoning goes through
`ClaudeService.review_clauses`. This keeps model-specific concerns (auth,
timeouts, retries, response parsing) in one place.
"""

import json
import logging
from dataclasses import dataclass

import anthropic

from app.core.config import get_settings
from app.core.exceptions import ClaudeRefusalError, ClaudeResponseInvalidError, ClaudeServiceError

logger = logging.getLogger(__name__)


@dataclass
class ClaudeReviewResult:
    findings: list[dict]
    model: str
    stop_reason: str
    input_tokens: int
    output_tokens: int


class ClaudeService:
    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        self._client = client

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            settings = get_settings()
            if not settings.ANTHROPIC_API_KEY:
                raise ClaudeServiceError("ANTHROPIC_API_KEY is not configured.")
            self._client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                timeout=settings.CLAUDE_TIMEOUT_SECONDS,
                max_retries=settings.CLAUDE_MAX_RETRIES,
            )
        return self._client

    def review_clauses(self, system: str, user_message: str, json_schema: dict) -> ClaudeReviewResult:
        settings = get_settings()

        try:
            response = self.client.messages.create(
                model=settings.CLAUDE_MODEL,
                max_tokens=settings.CLAUDE_MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user_message}],
                output_config={
                    "format": {"type": "json_schema", "schema": json_schema},
                    "effort": "high",
                },
            )
        except anthropic.APIConnectionError as exc:
            logger.exception("Could not connect to Claude")
            raise ClaudeServiceError("Could not connect to Claude.") from exc
        except anthropic.RateLimitError as exc:
            logger.warning("Claude rate limit exceeded: %s", exc)
            raise ClaudeServiceError("Claude rate limit exceeded.") from exc
        except anthropic.APIStatusError as exc:
            logger.exception("Claude API returned an error status")
            raise ClaudeServiceError(f"Claude API error: {exc.message}") from exc

        if response.stop_reason == "refusal":
            raise ClaudeRefusalError("Claude declined to review this document.")

        if response.stop_reason == "max_tokens":
            raise ClaudeResponseInvalidError(
                "Claude's response was truncated before completion."
            )

        text = next((block.text for block in response.content if block.type == "text"), None)
        if text is None:
            raise ClaudeResponseInvalidError("Claude did not return a text response.")

        try:
            payload = json.loads(text)
            findings = payload["findings"]
            if not isinstance(findings, list):
                raise TypeError("findings must be a list")
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ClaudeResponseInvalidError(
                "Claude's response was not valid structured JSON."
            ) from exc

        usage = response.usage
        return ClaudeReviewResult(
            findings=findings,
            model=response.model,
            stop_reason=response.stop_reason,
            input_tokens=usage.input_tokens if usage else 0,
            output_tokens=usage.output_tokens if usage else 0,
        )


claude_service = ClaudeService()
