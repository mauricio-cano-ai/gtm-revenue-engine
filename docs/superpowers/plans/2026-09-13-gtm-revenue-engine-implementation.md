# GTM Revenue Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portfolio-ready, locally runnable GTM revenue engine that accepts enriched prospect records, normalizes and deduplicates them, calculates an explainable composite score, routes accounts, and produces HubSpot-compatible CRM payloads with Clay and n8n integration artifacts.

**Architecture:** Python/pandas contains deterministic data transformation and scoring logic; CRM behavior is behind an adapter so the default demo is safe and offline. Clay is documented as the enrichment layer and n8n is supplied as an importable orchestration workflow that calls the deterministic Python/HTTP boundary and handles idempotency, retries, quarantine, and CRM sync.

**Tech Stack:** Python 3.11+, pandas, pydantic v2, PyYAML, requests, pytest, n8n workflow JSON, Clay setup documentation, PowerShell demo runner.

**Spec:** `docs/superpowers/specs/2026-09-13-gtm-revenue-engine-design.md`

## Global Constraints

- Local demo must run without external paid accounts.
- Secrets and provider credentials must never be committed.
- Composite score must remain deterministic and explainable with configurable weights.
- Clay is the enrichment layer; n8n is the orchestration layer; Python/pandas owns deterministic transformations and scoring.
- HubSpot is the reference CRM payload shape, but the runnable default uses a mock adapter.
- Routing thresholds: Tier A 80-100, Tier B 60-79, Tier C 40-59, low priority below 40.
- Every production Python behavior is introduced by a failing test first.
- Documentation must make failure modes, setup, handoff, replay safety, and demo flow explicit.

---

## File Structure

- `pyproject.toml` — package metadata, dependencies, pytest settings, CLI entrypoint.
- `.env.example`, `.gitignore`, `LICENSE` — safe repository defaults.
- `config/scoring.yaml` — signal weights, tier thresholds, freshness windows.
- `src/gtm_engine/models.py` — validated prospect, scoring, routing, CRM payload models.
- `src/gtm_engine/normalize.py` — domain/text/technology normalization and pandas record cleanup.
- `src/gtm_engine/dedupe.py` — deterministic duplicate-key generation and DataFrame deduplication.
- `src/gtm_engine/scoring.py` — config loading, freshness handling, explainable signal-group scoring.
- `src/gtm_engine/routing.py` — tier and action recommendation.
- `src/gtm_engine/crm.py` — HubSpot-compatible payload generation plus mock/real adapter interfaces.
- `src/gtm_engine/pipeline.py` — end-to-end deterministic record processing.
- `src/gtm_engine/cli.py` — demo CLI writing artifacts.
- `tests/` — unit and integration-style local tests.
- `data/` — sample raw and enriched data.
- `n8n/gtm-revenue-engine.workflow.json` — sanitized importable workflow.
- `docs/` — Clay, architecture, CRM mapping, failure modes, handoff, runbook, Loom outline.
- `scripts/demo.ps1` — one-command Windows demo.

---

### Task 1: Package Skeleton and Validated Domain Models

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `src/gtm_engine/__init__.py`
- Create: `src/gtm_engine/models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Produces: `ProspectRecord`, `ScoreBreakdown`, `RoutingDecision`, `CRMPayloadBundle` pydantic models.

- [ ] **Step 1: Write failing model validation tests**

```python
from pydantic import ValidationError
from gtm_engine.models import ProspectRecord


def test_prospect_requires_company_identity():
    try:
        ProspectRecord(person_name="Ada Lovelace")
    except ValidationError as exc:
        assert "company identity" in str(exc).lower()
    else:
        raise AssertionError("expected validation error")


def test_domain_is_normalized_on_model_input():
    record = ProspectRecord(company_name="Acme", domain="https://www.Acme.com/path")
    assert record.domain == "acme.com"
```

- [ ] **Step 2: Run tests and verify RED**

Run: `pytest tests/test_models.py -q`
Expected: import/module failure because models are not implemented.

- [ ] **Step 3: Implement minimal validated models**

Use pydantic v2. `ProspectRecord` accepts company and signal fields, requires either `company_name` or `domain`, and normalizes domain input. Keep optional fields nullable rather than inventing data.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `pytest tests/test_models.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

`git add . && git commit -m "feat: add GTM domain models"`

---

### Task 2: Normalization and Deduplication

**Files:**
- Create: `src/gtm_engine/normalize.py`
- Create: `src/gtm_engine/dedupe.py`
- Test: `tests/test_normalize.py`
- Test: `tests/test_dedupe.py`

**Interfaces:**
- Produces: `normalize_domain(value: str | None) -> str | None`
- Produces: `normalize_technology(value: str) -> str`
- Produces: `normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame`
- Produces: `prospect_identity_key(record: Mapping[str, Any]) -> str`
- Produces: `deduplicate_dataframe(df: pd.DataFrame) -> pd.DataFrame`

- [ ] **Step 1: Write failing normalization tests**

```python
import pandas as pd
from gtm_engine.normalize import normalize_domain, normalize_dataframe


def test_normalize_domain_removes_protocol_www_path_and_case():
    assert normalize_domain("HTTPS://WWW.Example.COM/about") == "example.com"


def test_normalize_dataframe_trims_text_and_normalizes_domains():
    df = pd.DataFrame([{"company_name": " Acme ", "domain": "www.Acme.com"}])
    out = normalize_dataframe(df)
    assert out.iloc[0]["company_name"] == "Acme"
    assert out.iloc[0]["domain"] == "acme.com"
```

- [ ] **Step 2: Verify RED, implement minimal normalization, verify GREEN**

Run targeted tests before and after implementation.

- [ ] **Step 3: Write failing dedupe tests**

```python
import pandas as pd
from gtm_engine.dedupe import deduplicate_dataframe


def test_dedupe_prefers_record_with_more_enrichment():
    df = pd.DataFrame([
        {"domain": "acme.com", "email": None, "employee_count": 100},
        {"domain": "https://www.acme.com", "email": "buyer@acme.com", "employee_count": 100},
    ])
    out = deduplicate_dataframe(df)
    assert len(out) == 1
    assert out.iloc[0]["email"] == "buyer@acme.com"
```

- [ ] **Step 4: Verify RED, implement identity-key and completeness preference, verify GREEN**

- [ ] **Step 5: Run `pytest tests/test_normalize.py tests/test_dedupe.py -q` and commit**

---

### Task 3: Configurable Composite Scoring and Routing

**Files:**
- Create: `config/scoring.yaml`
- Create: `src/gtm_engine/scoring.py`
- Create: `src/gtm_engine/routing.py`
- Test: `tests/test_scoring.py`
- Test: `tests/test_routing.py`

**Interfaces:**
- Produces: `load_scoring_config(path: str | Path) -> dict`
- Produces: `score_prospect(record: ProspectRecord, config: Mapping[str, Any], now: datetime | None = None) -> ScoreBreakdown`
- Produces: `route_score(score: int, config: Mapping[str, Any]) -> RoutingDecision`

- [ ] **Step 1: Write failing scoring tests**

Test a perfect-fit record receives 100, an empty-signal record stays low, and stale signals are discounted according to freshness config.

- [ ] **Step 2: Verify RED**

Run: `pytest tests/test_scoring.py -q`.

- [ ] **Step 3: Implement minimal weighted scoring**

The six groups map to the exact maxima in the spec. Each group is computed from explicit normalized features and returns both points and textual reasons; weights come from YAML.

- [ ] **Step 4: Verify GREEN**

- [ ] **Step 5: Write failing routing tests**

```python
from gtm_engine.routing import route_score


def test_tier_boundaries(scoring_config):
    assert route_score(80, scoring_config).tier == "A"
    assert route_score(79, scoring_config).tier == "B"
    assert route_score(60, scoring_config).tier == "B"
    assert route_score(59, scoring_config).tier == "C"
    assert route_score(39, scoring_config).tier == "LOW"
```

- [ ] **Step 6: Implement routing and verify all scoring/routing tests**

- [ ] **Step 7: Commit**

---

### Task 4: HubSpot-Compatible CRM Mapping and Safe Adapters

**Files:**
- Create: `src/gtm_engine/crm.py`
- Test: `tests/test_crm.py`

**Interfaces:**
- Produces: `build_hubspot_payloads(record, score, route) -> CRMPayloadBundle`
- Produces: `MockCRMAdapter.upsert(bundle) -> dict`
- Produces: `HubSpotCRMAdapter` with HTTP upsert methods guarded by environment configuration.

- [ ] **Step 1: Write failing CRM mapping tests**

Verify company and contact properties preserve source attribution, score, tier, sync timestamp, routing owner/action, and domain/email identifiers.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement payload builder and mock adapter**

Use HubSpot-compatible `/crm/v3/objects/companies` and `/contacts` property shapes without requiring network access.

- [ ] **Step 4: Add retry helper test for transient 429/5xx behavior**

Test the retry classifier is deterministic and never retries validation/4xx errors other than 429.

- [ ] **Step 5: Implement real adapter boundary and verify GREEN**

Real network calls are not used by tests or default demo.

- [ ] **Step 6: Commit**

---

### Task 5: End-to-End Pipeline and CLI Demo

**Files:**
- Create: `src/gtm_engine/pipeline.py`
- Create: `src/gtm_engine/cli.py`
- Create: `data/sample_prospects.csv`
- Create: `data/sample_enriched.json`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Produces: `process_dataframe(df, config, crm_adapter) -> list[dict]`
- CLI: `gtm-engine demo --input data/sample_prospects.csv --output artifacts`

- [ ] **Step 1: Write failing integration-style pipeline test**

Feed duplicate/sample records and assert output contains one processed account per identity, score breakdown, tier/action, CRM result, and deterministic `idempotency_key`.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Implement minimal pipeline**

Normalize -> deduplicate -> validate -> score -> route -> build CRM payload -> mock upsert -> structured result.

- [ ] **Step 4: Verify GREEN**

- [ ] **Step 5: Add CLI smoke test or invoke CLI against sample data**

- [ ] **Step 6: Commit**

---

### Task 6: n8n Orchestration Artifact

**Files:**
- Create: `n8n/gtm-revenue-engine.workflow.json`
- Create: `tests/test_n8n_artifact.py`

**Interfaces:**
- Workflow nodes: Clay Webhook, Validate Envelope, Idempotency Key, Quarantine Invalid, Score via Engine/API, Tier Branch, Build CRM Payload, Retry-aware CRM Upsert, Audit Result, Respond.

- [ ] **Step 1: Write artifact contract test**

Load workflow JSON and assert it is valid JSON, contains required named nodes, has no credentials IDs/secrets, and contains retry/error-flow metadata.

- [ ] **Step 2: Verify RED because artifact is absent**

- [ ] **Step 3: Build sanitized importable n8n workflow JSON**

Use environment expressions for endpoint/token values. Keep credential references absent so importing never leaks secrets.

- [ ] **Step 4: Verify GREEN and commit**

---

### Task 7: Documentation, Clay Setup, Failure Modes, and PowerShell Demo

**Files:**
- Create: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/clay-setup.md`
- Create: `docs/crm-mapping.md`
- Create: `docs/failure-modes.md`
- Create: `docs/handoff.md`
- Create: `docs/runbook.md`
- Create: `docs/loom-walkthrough.md`
- Create: `scripts/demo.ps1`
- Test: `tests/test_repository_contract.py`

**Interfaces:**
- PowerShell demo creates `.venv`, installs `.[dev]`, runs tests, executes CLI, and prints artifact paths.

- [ ] **Step 1: Write repository contract test**

Assert required docs, demo script, sample data, config, and n8n artifact exist; scan text artifacts for accidental secret patterns and forbidden employer-specific framing.

- [ ] **Step 2: Verify RED**

- [ ] **Step 3: Write documentation and demo script**

Clay documentation must specify multi-source table columns, enrichment waterfall, formulas, Claygent prompts with structured outputs, freshness columns, webhook body contract, and exact n8n handoff. Failure-mode doc must map each design failure to detection, mitigation, replay behavior, and audit outcome.

- [ ] **Step 4: Verify GREEN**

- [ ] **Step 5: Run complete verification**

Commands:
- `python -m pytest -q`
- `python -m gtm_engine.cli demo --input data/sample_prospects.csv --output artifacts`
- parse `n8n/gtm-revenue-engine.workflow.json` with Python JSON loader
- inspect generated `artifacts/processed_prospects.json`

- [ ] **Step 6: Commit**

`git add . && git commit -m "docs: complete GTM revenue engine handoff"`

---

## Self-Review

- Spec coverage: every success criterion maps to Tasks 2-7; local paid-account-free demo maps to Tasks 4-5; Clay/n8n evidence maps to Tasks 6-7.
- Placeholder scan: no implementation placeholder is permitted in repository deliverables; documentation examples must be executable or clearly labeled configuration examples.
- Type consistency: `ProspectRecord -> ScoreBreakdown -> RoutingDecision -> CRMPayloadBundle` is the single domain flow used by scoring, routing, CRM, pipeline, and CLI.
- Security: environment variables only for secrets; workflow JSON contains no credential IDs or tokens.
