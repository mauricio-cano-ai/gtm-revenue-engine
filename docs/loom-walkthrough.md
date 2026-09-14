# Loom Walkthrough Outline

Target length: 4-5 minutes.

## 0:00-0:30 — Business problem

"A GTM team has account data spread across sources, inconsistent enrichment, manual qualification, and CRM writes that can duplicate or fail. This system converts that into one monitored pipeline."

## 0:30-1:15 — Architecture

Show the README Mermaid diagram. Explain the boundaries in one sentence each: Clay enriches, n8n orchestrates, Python makes deterministic data/score decisions, CRM stores commercial state.

## 1:15-2:10 — Clay layer

Open `docs/clay-setup.md`. Point out the multi-source identity columns, Waterfall design, AI Formula/Conditional Run strategy, freshness timestamps, Claygent research schema, and HTTP API handoff.

Key line: "I use AI for semantic research, but final score thresholds and routing stay deterministic."

## 2:10-3:00 — Reliability

Open the n8n workflow. Walk left to right: webhook, validation/idempotency, quarantine, score call, tier routing, CRM upsert, retries, audit, response.

Then show `docs/failure-modes.md` and mention duplicate delivery, stale signals, rate limiting, partial failure, and replay.

## 3:00-4:00 — Code and demo

Run:

```powershell
.\scripts\demo.ps1
```

Show passing tests, `artifacts/summary.json`, then one processed record with score components, tier, idempotency key, and mock CRM IDs.

## 4:00-4:30 — Handoff

Show `docs/handoff.md`. Close with: "The design goal is that another GTM engineer can change providers, scoring policy, or CRM mapping without rebuilding the whole system or depending on the original author."
