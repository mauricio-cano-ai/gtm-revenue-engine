# Handoff

This repository is designed so a RevOps/GTM operator and an engineer can take ownership without the original builder.

## Ownership map

| Area | Owner | Change surface |
|---|---|---|
| ICP definition | GTM strategy / sales leadership | Clay formulas, scoring config inputs |
| enrichment providers | RevOps/GTM engineer | Clay Waterfall sequence and Conditional Runs |
| research prompt | GTM engineer | Claygent prompt + output schema |
| score weights/freshness | Revenue operations | `config/scoring.yaml` |
| deterministic transforms | Engineering/GTM engineer | `src/gtm_engine/` + tests |
| orchestration/retries | GTM engineer | n8n workflow |
| CRM fields/ownership | RevOps | CRM configuration + `docs/crm-mapping.md` |
| production incidents | GTM engineer + system owner | runbook + audit/quarantine store |

## Contract between layers

Clay sends normalized enrichment fields and signal timestamps. n8n validates the envelope and creates workflow-level idempotency before calling deterministic services. Python produces score reasons, routing, and CRM payloads. CRM writes must be idempotent and return object IDs/status for audit.

## What can change safely

- Score weights and freshness windows can change in YAML when the six groups still total 100 points.
- Clay providers can change without Python changes if the outbound normalized field contract stays stable.
- CRM can be replaced by a new adapter without changing scoring/routing.
- Research prompts can evolve as long as deterministic routing remains outside the LLM.

## What requires coordinated change

- Renaming outbound Clay fields requires matching n8n/Python schema changes.
- Changing company identity rules requires dedupe, CRM upsert, and idempotency review.
- Adding a new score group requires config, model, scoring tests, reporting, and stakeholder agreement because totals/benchmarks change.

## Handoff checklist

- Clone and run local tests.
- Execute the offline demo and inspect both artifacts.
- Import n8n workflow disabled.
- Configure test endpoints/environment variables.
- Build the Clay test table using `clay-setup.md`.
- Test duplicate, stale, partial, invalid, and retry cases.
- Confirm CRM custom properties and ownership mappings.
- Record a Loom walkthrough using `loom-walkthrough.md`.
- Activate on a small segment before scaling.
