# Dawa Verify

**AI-powered medicine verification, understanding and pharmacy assistant.**
_Piga picha ya dawa. Jua unachoshikilia._ ("Photograph the medicine. Know what you are holding.")

Built for **Hack for Humanity with Qwen**.

---

## Problem

Medicine packaging carries safety-critical information: product name, strength, manufacturer, batch number, expiry date, directions and warnings. It is often printed very small, damaged, or written in technical language, which is hard for people with limited literacy or poor eyesight to read. Small pharmacies, meanwhile, capture stock and batch data by hand, which is slow and error-prone, and expiry dates can be missed.

See [PROBLEM.md](PROBLEM.md) for the full problem statement.

## Proposed solution

A user or pharmacy worker photographs a medicine package. The system:

1. **See**: accepts one or more photos (front, back, batch/expiry area).
2. **Understand**: uses **Qwen Vision** to extract structured fields (name, strength, manufacturer, batch, expiry).
3. **Verify**: applies _deterministic_ rules (expiry, missing fields, reference-catalogue match) and reports evidence.
4. **Explain**: presents findings in plain language, with Swahili text and voice (text-to-speech) for accessibility.
5. **Act**: lets a pharmacy confirm the extracted data, store it as inventory and query batches nearing expiry.

### What Dawa Verify will not do

- It will **not** claim a medicine is genuine or counterfeit from a photo. Results are: _Information verified_, _Potential warning signs_, _Could not verify_, _Expiry warning_.
- It will **not** prescribe or alter dosage. It only explains instructions already printed on the package or leaflet, and keeps extracted text separate from AI interpretation.

See [docs/adr/](docs/adr/) for the reasoning behind each design decision.

## Architecture (planned)

```
Web UI (mobile-first)  ->  Django REST API  ->  Qwen Vision (extraction)
                                  |
                                  +-> Validation & rules (dates, fields, catalogue match)
                                  +-> Explanation service (Swahili text -> TTS audio)
                                  +-> PostgreSQL (products, batches, inventory, requests, references)
```

The model does visual understanding. Deterministic backend code does dates, inventory arithmetic and rules.

## Tech stack

| Layer     | Choice                                                                             |
| --------- | ---------------------------------------------------------------------------------- |
| AI        | Qwen Vision (multimodal extraction)                                                |
| Backend   | Python, Django REST Framework                                                      |
| Database  | PostgreSQL                                                                         |
| Interface | Web prototype first; WhatsApp is a later adapter                                   |
| Voice     | Text-to-speech for Swahili explanations (provider to be selected, see ADR backlog) |

## Current progress

- [x] Project defined; proposal written (scope, safety boundaries, data model, MVP)
- [x] Key design decisions recorded as ADRs (interface, backend, expiry convention, verification model, Qwen Vision integration, Swahili TTS)
- [x] Repository created with README and PROBLEM.md
- [x] Django project skeleton and full data model, migrated and verified against real PostgreSQL
- [x] Deterministic rules engine (expiry parsing, verification categories, 60-day query) — unit tested
- [x] REST API (`/api/verifications/`, `/api/inventory/`) — exercised with real HTTP requests
- [x] Qwen Vision extraction wired in and **confirmed working against the live API** (Qwen3.8-Max correctly read product/strength/manufacturer/dosage form from a real photo)
- [x] Web UI wired to the real API: photo upload → verify → live evidence-based result; "Add stock" and inventory table read/write real data
- [x] Swahili explanation: Qwen translation of printed instructions + Azure Speech (Kenyan `sw-KE` voice) synthesis, cached per verification — request/response handling unit-tested with mocks; **not yet exercised against live Azure credentials**, see `docs/0006-swahili-tts.md`
- [x] 44 automated backend tests, all passing
- [ ] Manual live verification of Azure Speech (`python manage.py test_swahili_speech`) once a key is available
- [ ] WhatsApp adapter (post-MVP)
- [ ] Demo script and rehearsal with prepared physical products

Note: the original static prototype included hardcoded "regulatory certified / 92% match / security seal verified" mockup content. That made unearned authenticity claims the proposal explicitly rules out (section 16), so it was replaced with the real evidence-based verification categories the API now returns.

## Run it locally

**Backend:** see `backend/README.md` (Django + PostgreSQL, `python manage.py runserver 127.0.0.1:8000`).

**Frontend:** serve this folder with any static file server (e.g. `python -m http.server 3000`) with the backend running on `http://127.0.0.1:8000`. If your frontend origin isn't already covered by the CORS defaults in `backend/config/settings.py`, set `CORS_ALLOWED_ORIGINS` in `backend/.env`. If the API runs elsewhere than `127.0.0.1:8000`, set `window.DAWA_API_BASE_URL` before `frontend/app.js` loads.


## MVP scope

**Must have:** upload images; extract fields where visible; deterministic expiry detection; small documented reference catalogue; clear verification categories with evidence; pharmacy confirm-and-store; upcoming-expiry list.
**Also planned:** Swahili responses and voice explanations.
**Later:** WhatsApp, side-by-side reference comparison, suspicious-product report.

## Data and trust

Reference products in the catalogue must each document their source. Marketplace or internet images are never labelled "fake" or "real" without reliable evidence. Where an official verification mechanism is accessible and permitted, it takes precedence over model-based visual judgement.

## Repository layout (planned)

```
docs/adr/        Architecture decision records
PROBLEM.md       Problem statement
README.md        This file
```

## License

To be decided by the team.
