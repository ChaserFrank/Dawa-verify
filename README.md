# Dawa Verify

**AI-powered medicine verification, understanding and pharmacy assistant.**
*Piga picha ya dawa. Jua unachoshikilia.* ("Photograph the medicine. Know what you are holding.")

Built for **Hack for Humanity with Qwen**.

---

## Problem

Medicine packaging carries safety-critical information: product name, strength, manufacturer, batch number, expiry date, directions and warnings. It is often printed very small, damaged, or written in technical language, which is hard for people with limited literacy or poor eyesight to read. Small pharmacies, meanwhile, capture stock and batch data by hand, which is slow and error-prone, and expiry dates can be missed.

See [PROBLEM.md](PROBLEM.md) for the full problem statement.

## Proposed solution

A user or pharmacy worker photographs a medicine package. The system:

1. **See**: accepts one or more photos (front, back, batch/expiry area).
2. **Understand**: uses **Qwen Vision** to extract structured fields (name, strength, manufacturer, batch, expiry).
3. **Verify**: applies *deterministic* rules (expiry, missing fields, reference-catalogue match) and reports evidence.
4. **Explain**: presents findings in plain language, with Swahili text and voice (text-to-speech) for accessibility.
5. **Act**: lets a pharmacy confirm the extracted data, store it as inventory and query batches nearing expiry.

### What Dawa Verify will not do

- It will **not** claim a medicine is genuine or counterfeit from a photo. Results are: *Information verified*, *Potential warning signs*, *Could not verify*, *Expiry warning*.
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

| Layer | Choice |
|---|---|
| AI | Qwen Vision (multimodal extraction) |
| Backend | Python, Django REST Framework |
| Database | PostgreSQL |
| Interface | Web prototype first; WhatsApp is a later adapter |
| Voice | Text-to-speech for Swahili explanations (provider to be selected, see ADR backlog) |

## Current progress

- [x] Project defined; proposal written (scope, safety boundaries, data model, MVP)
- [x] Key design decisions recorded as ADRs (interface, backend, expiry convention, verification model)
- [x] Repository created with README and PROBLEM.md
- [ ] Qwen Vision API access and first real extraction test (credits pending)
- [ ] Django project skeleton and data model
- [ ] Extraction service with strict JSON schema
- [ ] Deterministic rules: expiry and catalogue matching
- [ ] Web UI: upload and evidence-based result
- [ ] Pharmacy confirm-and-store flow and 60-day expiry query
- [ ] Swahili explanation and TTS
- [ ] Tests and demo script with prepared products

Nothing beyond the project definition is implemented yet. This section will be updated as work lands.

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
