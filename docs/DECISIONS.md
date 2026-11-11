# Technical decisions — Grok LIFE OS

## ADR-001: Local-first SQLite + FastAPI
Zero cost, Chromebook compatible, no required cloud.

## ADR-002: Ledger postings for finance
Account + Transaction + Posting avoids double-counting available vs reserved.

## ADR-003: In-process event bus
Simple pub/sub for module coupling in single process.

## ADR-004: Rules-first AI
NEXUS rules always on; LLM optional via env. Never fake external models.

## ADR-005: Independent repository
Only `grok-life-os`. Never write to other LIFE OS repos.

## ADR-006: No GitHub as personal database
Export/import JSON for portability.
