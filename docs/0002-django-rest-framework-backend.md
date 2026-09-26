# ADR 0002: Django REST Framework backend

**Status:** Accepted

## Context
The proposal allows FastAPI or Django REST Framework, with PostgreSQL.

## Decision
Use Django + DRF with PostgreSQL.

## Reasoning
- The ORM and migrations map directly onto the proposed data model (Product, Batch, InventoryItem, VerificationRequest, ProductReference).
- Django admin gives a ready way to maintain the reference catalogue and record the source of each reference product, which the proposal requires.
- The team knows the stack well, which lowers delivery risk.

## Consequences
- Slightly heavier than FastAPI for a pure API, accepted for the admin and ORM benefits.
- Batch identity is unique on `(product, batch_number)`, not `batch_number` alone.
