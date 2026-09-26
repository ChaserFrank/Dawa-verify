# ADR 0005: Qwen Vision integration via ModelScope, and the vision-support caveat

**Status:** Accepted, with an open verification item

## Context
Hackathon credits arrived for ModelScope's OpenAI-compatible API (`https://api-inference.modelscope.ai/v1`), with four models: `Qwen-Ambassador/Qwen3.7-Max`, `Qwen3.8-Max`, `Qwen3.8-plus`, `Qwen3.7-Plus`.

## Decision
Implement `QwenVisionExtractor` using the `openai` Python SDK against the given base URL, sending images as base64 `image_url` content blocks in an OpenAI-style chat completion, with a system prompt that requires a strict JSON response and forbids guessing ungrounded values.

## Caveat — resolved by a real test call

None of the four given model names carry ModelScope's `-VL-` naming used for its vision-capable models, and independent usage reports described `Qwen3.7 Plus` / `Qwen3.8 Max` being used for text-only tasks. This was flagged as unverified rather than assumed.

**Resolved 2026-09-25:** `python manage.py test_qwen_extraction` was run against a real photo with `QWEN_MODEL=Qwen-Ambassador/Qwen3.8-Max`. It correctly read product name, strength, manufacturer and dosage form off the package. **`Qwen3.8-Max` is vision-capable.** Batch number and expiry came back `null` on that test photo — expected when they aren't legible in the given image(s), not a bug; the schema requires `null` over a guess for exactly this case.

## Failure handling
`ExtractionFailed` (bad JSON, missing fields, transport error, empty response) is distinct from a normal "could not verify" result. The API returns `502` for it, never disguising an extraction pipeline failure as a calm verification outcome — this follows directly from ADR 0004: the two are different kinds of "we don't know," and only one of them is expected user-facing behaviour.

## Consequences
- The extractor's request/response handling is unit-tested with a mocked client (33 tests total, all passing), but that only proves *our* code is correct, not that the live model does what we assume.
- `QWEN_MODEL` is a separate env var from `QWEN_API_BASE`/`QWEN_API_KEY` so it can be swapped without a code change if a VL model becomes available.
