# Failure Modes and Replay Behavior

The system is designed so failures are visible, attributable, and replayable without silently duplicating downstream work.

| Failure mode | Detection | Mitigation | Replay / audit outcome |
|---|---|---|---|
| Duplicate webhook delivery | same deterministic idempotency key | reject already-completed key or reuse incomplete event | replay is safe; one commercial write |
| Partial enrichment | required/optional field checks + enrichment confidence | score only available signals; route Tier C when more enrichment is needed | preserve original payload and missing-field list |
| Stale signal data | compare signal timestamp with configured freshness window | discount stale signal and optionally trigger refresh | score reasons record stale signal penalty |
| Missing domain | validation allows company name fallback but marks weaker identity | quarantine when neither domain nor company name exists; enrich further before CRM when needed | retain source row and validation reason |
| Conflicting company identifiers | normalized domain disagrees with external/company ID | quarantine or require human resolution before merge | never silently merge conflicting company records |
| Malformed API response | schema/JSON validation fails | stop downstream write and capture response summary | event remains replayable after provider fix |
| HTTP 429 rate limiting | response status 429 | bounded retry with backoff / Retry-After | same idempotency key reused |
| Transient 5xx error | response status 500-599 | bounded retry then dead-letter/quarantine | audit attempts and terminal state |
| LLM invalid structured output | structured-output/schema validation | retry semantic step only when safe; otherwise keep deterministic fields and quarantine research result | routing threshold is never delegated to invalid AI output |
| CRM upsert failure | non-success CRM response or exception | no success audit; retain CRM payload and idempotency key | retry upsert without rebuilding a new identity |
| Timeout during enrichment or CRM sync | request exceeds configured timeout | bounded retry for transient endpoint; avoid unbounded waits | terminal timeout reason stored for replay |
| Replay after partial failure | event has same idempotency key but incomplete status | resume only incomplete downstream stage | prior completed stages are not duplicated |

## Dead-letter / quarantine record

Minimum fields:

```json
{
  "idempotency_key": "gtm:...",
  "status": "quarantined",
  "stage": "validation|scoring|crm",
  "reason": "human-readable reason",
  "source": "clay",
  "source_record_id": "...",
  "payload": {},
  "attempts": 1,
  "last_attempt_at": "ISO-8601"
}
```

A production implementation would persist this outside workflow execution history so operators can search and replay failures after n8n retention expires.
