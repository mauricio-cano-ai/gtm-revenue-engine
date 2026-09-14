# Runbook

## Local verification

From the repository root:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m gtm_engine.cli demo --input data/sample_prospects.csv --output artifacts --config config/scoring.yaml
```

Expected artifacts:

- `artifacts/processed_prospects.json`
- `artifacts/summary.json`

## n8n setup

Required environment variables for the sanitized workflow:

```text
GTM_ENGINE_SCORE_URL=<internal scoring endpoint>
GTM_CRM_UPSERT_URL=<internal CRM upsert endpoint>
```

The committed workflow intentionally contains no secret token or n8n credential reference. Add authentication in the deployment environment before production use.

## Pre-activation checks

1. Webhook accepts a valid test payload.
2. Invalid identity returns quarantine/422 behavior.
3. Duplicate row produces the same idempotency key.
4. Score output includes component reasons.
5. Tier boundaries match `config/scoring.yaml`.
6. CRM test/sandbox receives expected custom fields.
7. HTTP 429 and 5xx paths retry only a bounded number of times.
8. Terminal failures remain replayable with original payload and identity.

## Troubleshooting

### Unexpected low score

Inspect `score.components` and `score.reasons`. Check signal values and timestamps before changing weights. A stale intent signal is deliberately discounted.

### Duplicate CRM account

Check domain normalization first. Confirm the upstream row uses the same canonical domain and that CRM search/upsert is keyed by domain rather than display name.

### n8n retries repeatedly

Inspect response code. Retry 429/5xx and network/transient errors only. Validation errors should go to quarantine, not a retry loop.

### Clay row never reaches n8n

Check the HTTP API column run condition, row readiness/freshness conditions, n8n webhook URL, and the HTTP response stored in the Clay action cell.

### Clay enrichment costs rise unexpectedly

Audit Waterfall order and Conditional Runs. Do not rerun already-fresh enrichments. Use formulas for deterministic cleanup and reserve Claygent for semantic research where it adds information unavailable from structured providers.

## Replay procedure

1. Locate quarantined event and idempotency key.
2. Fix the underlying data/provider/config issue.
3. Do not generate a new identity for the same source event.
4. Replay from the earliest incomplete stage.
5. Verify previously completed CRM object IDs are reused.
6. Mark audit state complete only after the final write succeeds.
