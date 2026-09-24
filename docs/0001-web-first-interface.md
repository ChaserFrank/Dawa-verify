# ADR 0001: Web prototype first; WhatsApp deferred

**Status:** Accepted

## Context
The proposal lists a web prototype first and WhatsApp "if time permits". We must pick one and build it end to end.

## Decision
Build a mobile-first web interface. Keep the API channel-agnostic so WhatsApp can be added later as an adapter.

## Reasoning
- The pharmacy workflow (review, edit, confirm, store) needs an editable form and an inventory table, which chat handles poorly.
- A web app needs no external account setup, public webhook or media-download step, so it has fewer demo-time failure points.
- Camera capture and audio playback are native to browsers.

## Consequences
- Consumer reach via WhatsApp is deferred.
- Business logic must live in the API and services, never in the UI, so a second channel stays cheap.
