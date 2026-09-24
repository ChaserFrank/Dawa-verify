# ADR 0003: Expiry date convention

**Status:** Accepted (revisit if a product states an exact day)

## Context
Packaging usually prints expiry as month and year (e.g. "08/2027") with no day. Expiry checks and the "expires within N days" query must be deterministic and consistent.

## Decision
- A month-year expiry is treated as valid **through the last day of that month**.
- If an exact day is printed, use it.
- Expiry status and day counts are computed in backend code, never by the model.
- The extracted value is stored as printed (raw text) alongside the parsed date.

## Reasoning
This is the conventional reading of month-year expiry and avoids falsely flagging a medicine as expired during its final month. Storing the raw text preserves the distinction between extraction and interpretation.

## Consequences
- Example: a batch expiring 11/2026 expires on 30 Nov 2026, which is outside a 60-day window measured from 24 Sep 2026. Demo data must be prepared with this in mind.
- Ambiguous or unparseable dates yield "Could not verify", never a guess.
