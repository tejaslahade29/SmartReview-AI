"""Free-tier alternative to ClaudeService, with the exact same interface.

review_engine.py picks between this and ClaudeService based on
settings.AI_PROVIDER — neither the prompt builder, the validator, nor the
review engine's persistence logic needs to know which one ran. Findings
are re-validated downstream regardless of provider (review_validator.py),
so this does not need to replicate Claude's strict schema enforcement —
it asks for JSON, and untrusted/malformed output is dropped later either way.
"""

import json
import logging
import time
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.exceptions import AIRefusalError, AIResponseInvalidError, AIServiceError

logger = logging.getLogger(__name__)

_REFUSAL_FINISH_REASONS = {"SAFETY", "RECITATION", "PROHIBITED_CONTENT", "BLOCKLIST"}

# Gemini's free tier regularly answers 503 "high demand" / 429 for a few
# seconds at a time. Retry those with backoff, then try a lighter fallback
# model before giving up. Anything else (bad key, bad request) fails fast.
_TRANSIENT_CODES = {429, 500, 503, 504}
_RETRY_DELAYS_SECONDS = (2, 5, 10)
_FALLBACK_MODELS = ("gemini-2.5-flash", "gemini-2.5-flash-lite")


@dataclass
class GeminiReviewResult:
    findings: list[dict]
    model: str
    stop_reason: str
    input_tokens: int
    output_tokens: int


def _to_gemini_schema(schema: dict) -> dict:
    """Gemini's response_schema only supports a constrained OpenAPI-style
    subset of JSON Schema — no `additionalProperties`, no `type` unions for
    nullability. Strips what it doesn't understand rather than failing;
    the real validation happens in review_validator.py regardless.
    """
    if not isinstance(schema, dict):
        return schema

    result = {}
    for key, value in schema.items():
        if key == "additionalProperties":
            continue
        if key == "type" and isinstance(value, list):
            non_null = [t for t in value if t != "null"]
            result[key] = non_null[0] if non_null else "string"
        elif key == "properties" and isinstance(value, dict):
            result[key] = {k: _to_gemini_schema(v) for k, v in value.items()}
        elif key == "items":
            result[key] = _to_gemini_schema(value)
        else:
            result[key] = value
    return result


class GeminiService:
    def __init__(self, client: "genai.Client | None" = None) -> None:
        self._client = client

    @property
    def client(self) -> "genai.Client":
        if self._client is None:
            settings = get_settings()
            if not settings.GEMINI_API_KEY:
                raise AIServiceError("GEMINI_API_KEY is not configured.")
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    def review_clauses(self, system: str, user_message: str, json_schema: dict) -> GeminiReviewResult:
        settings = get_settings()

        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=_to_gemini_schema(json_schema),
            max_output_tokens=settings.GEMINI_MAX_OUTPUT_TOKENS,
            http_options=types.HttpOptions(timeout=int(settings.GEMINI_TIMEOUT_SECONDS * 1000)),
        )
        models = [settings.GEMINI_MODEL, *(m for m in _FALLBACK_MODELS if m != settings.GEMINI_MODEL)]
        attempts = [(models[0], delay) for delay in (0, *_RETRY_DELAYS_SECONDS)]
        attempts += [(m, 0) for m in models[1:]]

        response = None
        used_model = settings.GEMINI_MODEL
        last_exc: Exception | None = None
        for model, delay in attempts:
            if delay:
                time.sleep(delay)
            try:
                response = self.client.models.generate_content(model=model, contents=user_message, config=config)
                used_model = model
                break
            except Exception as exc:  # SDK error taxonomy isn't guaranteed stable across versions
                last_exc = exc
                logger.warning("Gemini call failed on %s: %s", model, exc)
                if getattr(exc, "code", None) not in _TRANSIENT_CODES:
                    break

        if response is None:
            logger.error("Gemini API call failed", exc_info=last_exc)
            raise AIServiceError(f"Gemini API error: {last_exc}") from last_exc

        candidates = response.candidates or []
        finish_reason = str(candidates[0].finish_reason) if candidates else "UNKNOWN"

        if any(reason in finish_reason for reason in _REFUSAL_FINISH_REASONS):
            raise AIRefusalError("Gemini declined to review this document.")

        if "MAX_TOKENS" in finish_reason:
            raise AIResponseInvalidError("Gemini's response was truncated before completion.")

        text = response.text
        if not text:
            raise AIResponseInvalidError("Gemini did not return a text response.")

        try:
            payload = json.loads(text)
            findings = payload["findings"]
            if not isinstance(findings, list):
                raise TypeError("findings must be a list")
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise AIResponseInvalidError("Gemini's response was not valid structured JSON.") from exc

        usage = response.usage_metadata
        return GeminiReviewResult(
            findings=findings,
            model=used_model,
            stop_reason=finish_reason,
            input_tokens=usage.prompt_token_count if usage else 0,
            output_tokens=usage.candidates_token_count if usage else 0,
        )


gemini_service = GeminiService()
