"""
Swahili explanation: translate printed_instructions (exactly as extracted
from the package -- never anything else) into simple Swahili via Qwen,
then synthesize it to audio via Azure Cognitive Services Speech.

Per ADR 0004/0006: this explains what is already printed. It never adds,
removes, or reinterprets dosage information, and it refuses outright if
there is no printed_instructions to translate -- it does not invent a
generic "take as directed" filler.
"""
from __future__ import annotations

import dataclasses

import requests
from django.conf import settings

_TRANSLATION_SYSTEM_PROMPT = (
    "You translate medicine usage instructions from English (or whatever "
    "language they are given in) into simple, clear Swahili suitable for "
    "reading aloud to someone with limited literacy. Rules:\n"
    "- Translate ONLY what is given. Do not add dosage, warnings, or "
    "advice that is not present in the source text.\n"
    "- Do not soften, remove, or change any number, frequency, or timing.\n"
    "- Keep it short and conversational, not clinical.\n"
    "- Respond with ONLY the Swahili translation text. No preamble, no "
    "English, no quotation marks."
)


class TranslationFailed(Exception):
    pass


class SpeechSynthesisFailed(Exception):
    pass


class SpeechNotConfigured(Exception):
    pass


def translate_to_swahili(instructions_text: str) -> str:
    """Calls Qwen (text-only) to translate printed instructions. Reuses
    the same QWEN_API_KEY/BASE/MODEL as extraction -- confirmed working
    against Qwen3.8-Max for vision; this is a plain text chat completion,
    which is an even simpler case for the same model/endpoint.
    """
    if not settings.QWEN_API_KEY or not settings.QWEN_API_BASE or not settings.QWEN_MODEL:
        raise TranslationFailed("Qwen is not configured (QWEN_API_KEY/BASE/MODEL).")

    from openai import OpenAI

    client = OpenAI(api_key=settings.QWEN_API_KEY, base_url=settings.QWEN_API_BASE)
    try:
        response = client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=[
                {"role": "system", "content": _TRANSLATION_SYSTEM_PROMPT},
                {"role": "user", "content": instructions_text},
            ],
            temperature=0,
            max_tokens=300,
        )
    except Exception as exc:  # noqa: BLE001
        raise TranslationFailed(f"Qwen translation request failed: {exc}") from exc

    if not response.choices or not (response.choices[0].message.content or "").strip():
        raise TranslationFailed("Qwen returned an empty translation.")

    return response.choices[0].message.content.strip()


@dataclasses.dataclass
class SynthesizedAudio:
    content: bytes
    content_type: str  # e.g. "audio/mpeg"


def synthesize_swahili_speech(swahili_text: str) -> SynthesizedAudio:
    """Calls Azure Cognitive Services Speech (REST, not the SDK, to avoid
    an extra heavy dependency) to synthesize `swahili_text` as audio using
    a Kenyan Swahili neural voice.

    NOT verified against the live Azure endpoint from this development
    environment (network egress here does not reach *.tts.speech.microsoft.com).
    Run `manage.py test_swahili_speech "<some Swahili text>"` against real
    credentials before the demo -- see ADR 0006.
    """
    if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
        raise SpeechNotConfigured("AZURE_SPEECH_KEY / AZURE_SPEECH_REGION are not set.")

    endpoint = f"https://{settings.AZURE_SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    ssml = (
        '<speak version="1.0" xml:lang="sw-KE">'
        f'<voice name="{settings.AZURE_SPEECH_VOICE}">{_escape_ssml(swahili_text)}</voice>'
        "</speak>"
    )
    headers = {
        "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-64kbitrate-mono-mp3",
        "User-Agent": "dawa-verify",
    }

    try:
        response = requests.post(endpoint, headers=headers, data=ssml.encode("utf-8"), timeout=20)
    except requests.RequestException as exc:
        raise SpeechSynthesisFailed(f"Azure Speech request failed: {exc}") from exc

    if response.status_code != 200:
        raise SpeechSynthesisFailed(
            f"Azure Speech returned {response.status_code}: {response.text[:500]}"
        )
    if not response.content:
        raise SpeechSynthesisFailed("Azure Speech returned an empty audio body.")

    return SynthesizedAudio(content=response.content, content_type="audio/mpeg")


def _escape_ssml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
