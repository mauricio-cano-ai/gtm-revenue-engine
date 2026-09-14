# GTM Revenue Engine — Design Specification

Date: 2026-09-13
Owner: Mauricio Alfonso Cano
Target evidence: GTM Engineer / Revenue Systems / Clay + n8n + AI Automation

## 1. Objective

Build a production-style, portfolio-ready GTM system that demonstrates end-to-end ownership of lead sourcing, enrichment, signal scoring, routing, CRM synchronization, observability, and documentation.

The project must look like a reusable revenue-operations system, not a one-off job-application demo. It should be understandable by a GTM strategist, RevOps operator, and engineer without reading every implementation detail.

## 2. Success Criteria

The repository must demonstrate:

- Clay multi-source lead table design.
- Waterfall enrichment and fallback logic.
- Formula-based normalization and qualification.
- Claygent / LLM-assisted research and classification.
- n8n multi-step orchestration with webhooks, branching, retries, deduplication, and recovery.
- Python + pandas data cleaning, normalization, enrichment preparation, and composite scoring.
- API/webhook-first integrations.
- CRM handoff with HubSpot-compatible contact/company/deal payloads and bidirectional-sync design.
- Composite scoring across firmographic, technographic, hiring, funding, intent, and behavioral signals.
- Explicit failure-mode handling.
- Operational documentation: README, architecture, handoff notes, runbook, test instructions, and Loom walkthrough outline.

## 3. Positioning

Repository name: `gtm-revenue-engine`

Public positioning:

> A production-style GTM orchestration system that turns multi-source prospect data into enriched, scored, routed, CRM-ready opportunities using Clay, n8n, Python/pandas, APIs/webhooks, and LLM-assisted research.

The repository must not mention ATQLeads in its name or core architecture. A short “role relevance” section may map capabilities to common GTM engineering responsibilities without implying the project was commissioned by an employer.

## 4. Architecture

### 4.1 Clay — Data & Enrichment Layer

Clay owns initial prospect-table enrichment and signal collection.

Expected table concepts:

- company domain
- company name
- person name / title
- LinkedIn URL
- location
- industry
- employee count
- company stage
- technologies
- hiring signals
- funding signals
- intent signals
- behavioral signals
- email / phone availability
- enrichment confidence
- source freshness

Clay design includes:

1. Multi-source table inputs.
2. Waterfall enrichment with ordered providers / fallbacks.
3. Formula columns for normalization and derived attributes.
4. Claygent prompts for account research, ICP-fit reasoning, and message context.
5. Per-signal freshness fields.
6. Webhook/API handoff into n8n.

Secrets or paid-provider credentials are never committed.

## 5. n8n — Orchestration Layer

n8n receives enriched prospect records through a webhook and manages workflow state.

Core workflow:

1. Receive Clay webhook.
2. Validate required fields and schema version.
3. Generate deterministic idempotency key.
4. Reject or quarantine malformed payloads.
5. Normalize the event.
6. Call Python scoring service or script.
7. Branch by score / ICP tier / signal confidence.
8. Produce CRM-ready payload.
9. Upsert company/contact.
10. Attach source and score metadata.
11. Route qualified accounts.
12. Record result and workflow status.
13. Return structured response.

Reliability requirements:

- retry/backoff for transient API failures
- deduplication
- idempotent writes
- dead-letter / quarantine path
- timeout handling
- explicit success/failure statuses
- replay-safe processing
- audit-friendly structured logging

A sanitized importable n8n workflow JSON will be included.

## 6. Python / pandas — Data & Scoring Layer

Python handles transformations that are clearer and more testable in code than in no-code expressions.

Modules:

- schema validation
- text/domain normalization
- deduplication
- missing-value handling
- technology normalization
- signal freshness calculation
- composite score calculation
- routing recommendation
- CRM payload creation

### Composite score

The score is intentionally explainable, not an opaque ML model.

Initial signal groups:

- Firmographic fit: 0–25
- Technographic fit: 0–15
- Hiring signal: 0–15
- Funding / growth signal: 0–15
- Intent signal: 0–20
- Behavioral signal: 0–10

Total: 0–100

Example tiers:

- 80–100: Tier A — immediate routing
- 60–79: Tier B — nurture / targeted outbound
- 40–59: Tier C — enrich further
- <40: Disqualify / low priority

Weights remain configurable in YAML/JSON rather than hard-coded into business logic.

## 7. CRM Integration

Primary reference implementation: HubSpot-compatible REST payloads.

The repository will demonstrate:

- company upsert strategy
- contact upsert strategy
- association strategy
- lead/account score fields
- source attribution fields
- routing-owner field
- sync timestamp
- workflow status
- deduplication strategy

Actual credentials remain optional. A mock CRM adapter is the default runnable path so the repository can be cloned and tested without a paid account.

A real HubSpot sandbox/test account can later be connected through environment variables without changing core business logic.

## 8. LLM / Claygent Use

LLM calls are used only where semantic reasoning is useful.

Examples:

- summarize account relevance
- classify ICP fit from public company text
- extract a concise buying-trigger hypothesis
- generate structured research notes
- suggest message context

LLM output must use structured schemas and validation. Critical routing and final score thresholds remain deterministic.

## 9. Failure Modes

The project explicitly documents and tests:

- duplicate webhook delivery
- partial enrichment
- stale signal data
- missing domain
- conflicting company identifiers
- malformed API response
- HTTP 429 / rate limiting
- transient 5xx errors
- LLM invalid structured output
- CRM upsert failure
- timeout during enrichment or CRM sync
- replay after partial failure

Fallback behavior must preserve data and prevent silent duplication.

## 10. Repository Structure

```text
gtm-revenue-engine/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── pyproject.toml
├── config/
│   └── scoring.yaml
├── data/
│   ├── sample_prospects.csv
│   └── sample_enriched.json
├── docs/
│   ├── architecture.md
│   ├── clay-setup.md
│   ├── crm-mapping.md
│   ├── failure-modes.md
│   ├── handoff.md
│   ├── runbook.md
│   ├── loom-walkthrough.md
│   └── superpowers/specs/...
├── n8n/
│   └── gtm-revenue-engine.workflow.json
├── src/gtm_engine/
│   ├── __init__.py
│   ├── models.py
│   ├── normalize.py
│   ├── dedupe.py
│   ├── scoring.py
│   ├── routing.py
│   ├── crm.py
│   └── cli.py
├── tests/
│   ├── test_normalize.py
│   ├── test_dedupe.py
│   ├── test_scoring.py
│   └── test_crm.py
└── scripts/
    └── demo.ps1
```

## 11. Demo Flow

The local demo must run without external paid accounts.

PowerShell demo:

1. Create virtual environment.
2. Install package and test dependencies.
3. Run tests.
4. Load sample prospect data.
5. Normalize and deduplicate.
6. Apply configurable composite scoring.
7. Generate routing decision.
8. Produce mock HubSpot-compatible payloads.
9. Save output under `artifacts/`.

The Clay/n8n integration path is documented separately and can be connected when credentials/accounts are available.

## 12. Testing Strategy

Required tests:

- normalization determinism
- domain/email normalization
- duplicate detection
- score boundaries
- missing-signal behavior
- freshness penalty behavior
- tier routing
- CRM payload shape
- idempotency-key stability

The project must ship with a passing local test suite.

## 13. Documentation Standard

README must answer in under one minute:

1. What problem does this solve?
2. What enters the system?
3. What happens to the data?
4. How is a lead scored and routed?
5. How does Clay connect to n8n?
6. Where does Python add value?
7. How does the CRM sync work?
8. What happens when something fails?
9. How do I run the demo?

Documentation is part of the artifact, not an afterthought.

## 14. GitHub Evidence Strategy

The repo should visibly demonstrate these hiring signals:

- GTM systems thinking
- revenue-funnel awareness
- Clay knowledge
- n8n production orchestration
- Python/pandas competence
- API/webhook integration
- CRM configuration thinking
- LLM integration with deterministic guardrails
- documentation and handoff discipline
- failure-mode planning
- independent execution

## 15. Non-Goals

To keep the project focused:

- no frontend dashboard in v1
- no paid enrichment-provider dependency required to run locally
- no bulk email sender implementation
- no attempt to recreate Clay
- no black-box ML scoring model
- no employer-specific branding

## 16. Completion Definition

Version 1 is complete when:

- `pytest` passes.
- the PowerShell demo produces deterministic artifacts.
- the n8n workflow imports successfully.
- Clay setup is documented with concrete table/column/prompt examples.
- HubSpot-compatible mapping is documented and mock-tested.
- architecture/failure-mode/runbook/handoff documentation is complete.
- README links directly to the most relevant technical evidence.
- the repository is suitable to link directly from a one-page resume.
