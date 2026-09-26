# Dawa Verify — backend

Django REST Framework API. See the repo-root README for the project overview.

## Local setup

1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Create a PostgreSQL database and user, then copy `.env.example` to `.env` and fill in the values.
4. `python manage.py migrate`
5. `python manage.py test verification` — 25 tests, all passing as of this commit.
6. `python manage.py runserver 127.0.0.1:8000`

## What's real vs. stubbed right now

- **Real:** models, migrations (run against Postgres, not sqlite), deterministic expiry/verification rules (`verification/rules.py`), the `/api/verifications/` and `/api/inventory/` endpoints, and the full test suite. All of this has been exercised with real HTTP requests against a running Postgres-backed server, not just unit tests.
- **Stubbed, clearly labelled:** `verification/extraction.py`'s `StubExtractor` returns an honestly-empty result (all fields `null`) whenever `QWEN_API_KEY` is unset. It is never allowed to fabricate plausible-looking medicine data. Once Qwen credits arrive, implement `QwenVisionExtractor.extract()` against the real API and re-run the full test suite plus a live manual check before trusting it.

## Key design decisions

See `../docs/adr/`:
- 0001 — web-first interface
- 0002 — Django REST Framework backend, and the `(product, batch_number)` uniqueness fix
- 0003 — expiry-date parsing convention (month/year -> last day of month)
- 0004 — verification categories and the safety boundary (no fake/real claims)

## API summary

`POST /api/verifications/` — multipart, field `images` (1+ files). Returns a verification result: category, evidence list, and the raw extraction.

`GET /api/inventory/` — list stock. Optional `?expires_within=<days>`.

`POST /api/inventory/` — confirm a batch into stock. JSON body: `product_name, manufacturer, strength, dosage_form, batch_number, expiry_raw_text, quantity, location`.

## Wiring in real Qwen Vision (once credits are in your `.env`)

1. Fill in `QWEN_API_KEY`, `QWEN_API_BASE`, `QWEN_MODEL` in `.env`.
2. **Before trusting it for anything**, run:
   ```
   python manage.py test_qwen_extraction path/to/a/real/medicine/photo.jpg
   ```
   This makes one real, billed API call and prints the parsed result. See ADR 0005 for why this step isn't optional — the given model names don't confirm image-input support, and this project's own network setup couldn't verify it during development.
3. If it works, `/api/verifications/` automatically switches from `StubExtractor` to `QwenVisionExtractor` — no other code change needed.
4. If it fails with something like "model does not support this input type," the model isn't vision-capable; try one of the other three, or ask the organizers for a `-VL-` model.

## Troubleshooting

**`relation "verification_..." does not exist`** — migrations haven't been applied to whatever database your `.env` currently points at. Run:
```
python manage.py showmigrations verification
python manage.py migrate
```
If this happens after previously working, the database was likely reset (dropped/recreated, fresh container, new Postgres data directory) without re-running `migrate`.

**Frontend shows "Could not reach Dawa Verify: Failed to fetch"** — this is CORS, not a backend crash; the browser blocked the request before it reached Django. Check what origin your browser's address bar shows for the frontend, and either confirm it's covered by the defaults in `config/settings.py` (`localhost`/`127.0.0.1`/`0.0.0.0` on ports 3000, 5500, 8080, 5173) or add it explicitly via `CORS_ALLOWED_ORIGINS` in `.env` (comma-separated, no trailing slash).

## Wiring in Swahili audio (once you have an Azure Speech key)

1. Create an Azure Speech resource (free F0 tier works for a demo) and get its key + region.
2. Fill in `AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION` in `.env`.
3. Verify before trusting it:
   ```
   python manage.py test_swahili_speech "Take one tablet twice daily after meals."
   ```
   This makes real, billed Qwen + Azure calls and saves an mp3 locally. See ADR 0006 — this step matters because the Azure request/response handling was written from documentation and mock-tested only; this environment couldn't reach Azure to verify it live.
4. Once that works, `POST /api/verifications/<id>/speak/` automatically does the real thing — nothing else to wire.
