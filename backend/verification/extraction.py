"""
Medicine-package extraction.

Defines the extractor interface the rest of the app depends on, plus:

- StubExtractor: used whenever settings.QWEN_API_KEY is empty. Returns a
  clearly-marked "not yet extracted" result -- never invented data.
- QwenVisionExtractor: calls the real Qwen Vision model via ModelScope's
  OpenAI-compatible API (per the Hack for Humanity credits email).

IMPORTANT CAVEAT (documented, not silently assumed): the model names given
in the hackathon credits email (Qwen3.7-Max, Qwen3.8-Max, Qwen3.8-plus,
Qwen3.7-Plus) do not carry the "-VL-" naming ModelScope uses for its
vision-capable models. This code sends image content exactly as the
OpenAI vision API spec requires, but whether the configured QWEN_MODEL
actually reads images has NOT been verified against the live API from
this environment (network egress here does not reach modelscope.ai).
Run `python manage.py test_qwen_extraction <image_path>` against the real
credentials before trusting this for a demo.
"""
from __future__ import annotations

import base64
import dataclasses
import json
import mimetypes
from typing import List, Optional

from django.conf import settings


@dataclasses.dataclass
class ExtractionResult:
    extractor_name: str
    product_name: Optional[str]
    strength: Optional[str]
    manufacturer: Optional[str]
    dosage_form: Optional[str]
    batch_number: Optional[str]
    expiry_raw_text: Optional[str]
    printed_instructions: Optional[str]
    confidence: Optional[float]  # 0.0-1.0, or None if the extractor doesn't provide one
    raw_response: dict  # kept verbatim for VerificationRequest.extracted_data

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


class ExtractionNotConfigured(Exception):
    """Raised when a real extractor is selected but has no credentials yet."""


class ExtractionFailed(Exception):
    """Raised when the Qwen API call succeeds at the HTTP level but the
    response cannot be turned into a usable result (bad JSON, API-level
    error, empty choices, etc.). Callers must not treat this as
    "no medicine detected" -- it's a distinct failure mode and should
    surface as an error, not a false "could not verify".
    """


class BaseExtractor:
    name: str = "base"

    def extract(self, image_paths: List[str]) -> ExtractionResult:
        raise NotImplementedError


class StubExtractor(BaseExtractor):
    """Deterministic, honestly-labelled placeholder. See module docstring."""

    name = "stub-v1"

    def extract(self, image_paths: List[str]) -> ExtractionResult:
        return ExtractionResult(
            extractor_name=self.name,
            product_name=None,
            strength=None,
            manufacturer=None,
            dosage_form=None,
            batch_number=None,
            expiry_raw_text=None,
            printed_instructions=None,
            confidence=None,
            raw_response={
                "note": (
                    "Qwen Vision is not configured yet (QWEN_API_KEY is empty). "
                    "This is a placeholder result, not a real extraction."
                ),
                "image_count": len(image_paths),
            },
        )


EXTRACTION_SCHEMA_FIELDS = [
    "product_name",
    "strength",
    "manufacturer",
    "dosage_form",
    "batch_number",
    "expiry_raw_text",
    "printed_instructions",
    "confidence",
]

_SYSTEM_PROMPT = (
    "You read photographs of medicine packaging and extract only what is "
    "visibly printed on the package. You never guess, infer, or fill in a "
    "plausible-sounding value for anything you cannot actually read. "
    "Respond with ONLY a single JSON object, no markdown fences, no "
    "commentary, with exactly these keys:\n"
    '{"product_name": string or null, "strength": string or null, '
    '"manufacturer": string or null, "dosage_form": string or null, '
    '"batch_number": string or null, "expiry_raw_text": string or null '
    '(copy the expiry EXACTLY as printed, e.g. "08/2027" or "15/08/2027" '
    'or "August 2027" -- do not reformat it), '
    '"printed_instructions": string or null (dosage/usage instructions '
    "exactly as printed, or null if none are visible), "
    '"confidence": number between 0 and 1 representing your overall '
    "confidence in the fields you were able to read}\n"
    "If a field is not visible or not legible in any of the photos, its "
    "value MUST be null. Do not leave any key out."
)


def _image_to_data_url(path: str) -> str:
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or "image/jpeg"
    with open(path, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _extract_json_object(text: str) -> dict:
    """Qwen models sometimes wrap JSON in ```json fences despite
    instructions not to. Strip those before parsing rather than failing.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


class QwenVisionExtractor(BaseExtractor):
    """Calls Qwen Vision through ModelScope's OpenAI-compatible API.

    See the module docstring for the unverified-vision-support caveat.
    """

    name = "qwen-vision"

    def __init__(self, api_key: str, api_base: str, model: str):
        if not api_key or not api_base or not model:
            raise ExtractionNotConfigured(
                "QWEN_API_KEY, QWEN_API_BASE and QWEN_MODEL must all be set."
            )
        from openai import OpenAI  # imported here so StubExtractor works without the package installed in envs that don't need it

        self.model = model
        self._client = OpenAI(api_key=api_key, base_url=api_base)

    def extract(self, image_paths: List[str]) -> ExtractionResult:
        if not image_paths:
            raise ValueError("extract() requires at least one image path.")

        content = [{"type": "text", "text": "Extract the fields from these medicine package photos."}]
        for path in image_paths:
            content.append({"type": "image_url", "image_url": {"url": _image_to_data_url(path)}})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": content},
                ],
                temperature=0,
                max_tokens=800,
            )
        except Exception as exc:  # noqa: BLE001 -- any transport/API error is a real failure to surface
            raise ExtractionFailed(f"Qwen API request failed: {exc}") from exc

        if not response.choices:
            raise ExtractionFailed("Qwen API returned no choices in the response.")

        raw_text = response.choices[0].message.content or ""
        try:
            parsed = _extract_json_object(raw_text)
        except json.JSONDecodeError as exc:
            raise ExtractionFailed(
                f"Qwen response was not valid JSON: {exc}. Raw response: {raw_text[:500]!r}"
            ) from exc

        missing_keys = [k for k in EXTRACTION_SCHEMA_FIELDS if k not in parsed]
        if missing_keys:
            raise ExtractionFailed(
                f"Qwen response JSON is missing expected keys: {missing_keys}. Got: {parsed!r}"
            )

        confidence = parsed.get("confidence")
        try:
            confidence = float(confidence) if confidence is not None else None
        except (TypeError, ValueError):
            confidence = None

        return ExtractionResult(
            extractor_name=self.name,
            product_name=parsed.get("product_name"),
            strength=parsed.get("strength"),
            manufacturer=parsed.get("manufacturer"),
            dosage_form=parsed.get("dosage_form"),
            batch_number=parsed.get("batch_number"),
            expiry_raw_text=parsed.get("expiry_raw_text"),
            printed_instructions=parsed.get("printed_instructions"),
            confidence=confidence,
            raw_response={
                "model": self.model,
                "raw_text": raw_text,
                "parsed": parsed,
            },
        )


def get_extractor() -> BaseExtractor:
    """Selects the extractor based on configuration -- the only place that
    decides stub vs. real, so tests and views never branch on settings.
    """
    if settings.QWEN_API_KEY and settings.QWEN_API_BASE and settings.QWEN_MODEL:
        return QwenVisionExtractor(settings.QWEN_API_KEY, settings.QWEN_API_BASE, settings.QWEN_MODEL)
    return StubExtractor()
