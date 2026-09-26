# ADR 0006: Swahili explanation via Qwen translation + Azure Speech TTS

**Status:** Accepted, with an open manual-verification item (same caveat class as ADR 0005)

## Context
The proposal's accessibility feature (section 6) needs printed medicine instructions explained in simple Swahili, with audio for people who struggle to read small labels. The user chose a cloud TTS service over the browser's Web Speech API for consistent voice quality.

## Decision
- **Translation:** Qwen (the same credentials already verified working for vision extraction) translates `extracted_data.printed_instructions` — exactly what was read off the package, nothing else — into simple Swahili. The prompt explicitly forbids adding, removing, or softening any dosage, frequency, or timing.
- **Synthesis:** Azure Cognitive Services Speech, via its REST endpoint (not the SDK, to avoid an extra heavy dependency), using a **Kenyan Swahili neural voice** — `sw-KE-RafikiNeural` or `sw-KE-ZuriNeural`, confirmed to exist in Azure's voice list (Google Cloud TTS's documented voice list does not clearly include an `sw-KE` voice, so Azure was the verified choice, not a default guess).
- **Both keys stay server-side.** The browser never sees `QWEN_API_KEY` or `AZURE_SPEECH_KEY`; it only calls our own `/api/verifications/<id>/speak/` endpoint.
- **No printed instructions → no explanation offered.** If `printed_instructions` is null (nothing legible on the package), `/speak/` returns 400. The system never fabricates a generic "take as directed" filler — this follows directly from ADR 0004.
- **Cached per verification.** Translation and synthesis are both billed calls; the result is stored on `VerificationRequest.swahili_text` / `swahili_audio` and reused on repeat requests, confirmed by test and by a live trace (first call: 201, both services invoked; second call: 200, no service calls).

## Caveat — not silently assumed away
This environment's network cannot reach `*.tts.speech.microsoft.com`, so `synthesize_swahili_speech()` has been verified with mocked responses only — the request format follows Azure's documented REST API (SSML body, `Ocp-Apim-Subscription-Key` header, `sw-KE` voice), but has not been exercised against a live Azure resource. Run `python manage.py test_swahili_speech "<some instructions text>"` against real `AZURE_SPEECH_KEY`/`AZURE_SPEECH_REGION` before the demo.

## Consequences
- Two more billed external services in the pipeline; both fail as distinct, visible errors (502 for a transport/response failure, 503 if not configured) rather than silently producing no audio.
- Requires an Azure Speech resource (F0 free tier is sufficient for a demo) — not provided by the Qwen hackathon credits, so this is a separate signup.
