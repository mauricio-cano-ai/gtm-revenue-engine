# Clay Setup

This document describes the production-facing enrichment layer. The local repository can run without Clay; this setup connects a real Clay workbook to the n8n orchestration layer.

## 1. Workbook and table

Create a workbook named `GTM Revenue Engine` and a primary table named `Account Enrichment`.

Recommended source/identity columns:

| Column | Type | Purpose |
|---|---|---|
| company_name | Text | canonical company name |
| company_domain_raw | Text | source-provided website/domain |
| company_domain | Formula/Text | normalized domain used as primary account key |
| person_name | Text | target contact |
| title | Text | current title |
| linkedin_url | URL/Text | person identifier |
| location | Text | geography |
| source | Text | list/webinar/inbound/intent/etc. |
| source_record_id | Text | immutable source-row ID |
| source_ingested_at | Date | original ingestion time |

A Formula column should normalize domain casing, protocol, `www`, and trailing path before any downstream match or CRM write. Use an AI Formula to generate the transformation if preferred, then inspect the produced logic before applying it at scale.

## 2. Enrichment waterfall

Use a Waterfall when multiple providers can return the same field. Typical waterfall targets:

- company firmographics
- work email
- mobile phone
- social/profile URL
- technology/technographic data

Order providers by the combination of coverage, geography, latency, and cost that fits the account segment. Preserve both the successful value and provider/source where useful for auditability.

Do not run every provider unconditionally. Waterfall behavior should stop after an acceptable result and should be paired with Conditional Runs where the row does not need enrichment.

## 3. Firmographic and technographic fields

Recommended normalized outputs:

- industry
- employee_count
- company_stage
- headquarters/location
- technologies
- firmographic_fit (0-1)
- technographic_fit (0-1)
- enrichment_confidence (0-1)

Formula logic should convert provider-specific categories into a stable internal vocabulary before the row leaves Clay.

## 4. Signal fields and freshness

Store each signal separately instead of collapsing everything into one opaque score:

| Signal | Value | Timestamp/freshness |
|---|---|---|
| hiring_signal | 0-1 | hiring_signal_at |
| funding_signal | 0-1 | funding_signal_at |
| intent_signal | 0-1 | intent_signal_at |
| behavioral_signal | 0-1 | behavioral_signal_at |

Add Formula columns such as `intent_is_fresh`, `funding_is_fresh`, and `needs_signal_refresh`. The Python scoring layer applies the authoritative freshness penalty, but Clay should use freshness for Conditional Runs so credits are not spent refreshing already-current data.

Example conditional intent:

```text
Run enrichment only if:
- company_domain exists
- required output is blank OR source freshness has expired
- row is not explicitly disqualified
```

## 5. Claygent research

Use Claygent for last-mile research that is hard to obtain from fixed provider schemas, not for deterministic routing decisions.

Suggested account-research prompt:

```text
Research the company at {{company_domain}}.
Use public company pages and recent public evidence.
Return concise structured fields:
1. icp_fit_reason: max 2 sentences
2. buying_trigger: max 1 sentence
3. relevant_technology_evidence: array of short strings
4. growth_or_hiring_evidence: array of short strings
5. evidence_urls: array of public URLs
6. confidence: number 0.0-1.0

Do not invent missing facts. If evidence is insufficient, return an empty value and reduce confidence.
```

Map outputs into:

- `research_summary`
- `buying_trigger`
- `claygent_confidence`
- evidence/source columns

A Conditional Run should prevent Claygent from executing when the account lacks a usable domain or when existing research is still fresh.

## 6. Reusable Clay Function

Once the table sequence is stable, save the reusable enrichment block as a Clay Function such as `Account ICP + Signal Enrichment`.

Inputs:

- company_domain
- company_name
- optional linkedin_url

Outputs:

- normalized firmographics
- normalized technologies
- selected contact data
- signal values/timestamps
- research summary/buying trigger
- enrichment confidence

Keeping the enrichment block reusable prevents table-to-table logic drift.

## 7. Send the row to n8n with HTTP API

After required enrichment is complete, add an `HTTP API` enrichment/action.

Method: `POST`

Endpoint: the production URL for the n8n `Clay Webhook` node.

Body shape:

```json
{
  "schema_version": "v1",
  "company_name": "{{company_name}}",
  "domain": "{{company_domain}}",
  "person_name": "{{person_name}}",
  "title": "{{title}}",
  "email": "{{work_email}}",
  "linkedin_url": "{{linkedin_url}}",
  "industry": "{{industry}}",
  "employee_count": "{{employee_count}}",
  "technologies": "{{technologies}}",
  "source": "{{source}}",
  "source_record_id": "{{source_record_id}}",
  "firmographic_fit": "{{firmographic_fit}}",
  "technographic_fit": "{{technographic_fit}}",
  "hiring_signal": "{{hiring_signal}}",
  "funding_signal": "{{funding_signal}}",
  "intent_signal": "{{intent_signal}}",
  "behavioral_signal": "{{behavioral_signal}}",
  "hiring_signal_at": "{{hiring_signal_at}}",
  "funding_signal_at": "{{funding_signal_at}}",
  "intent_signal_at": "{{intent_signal_at}}",
  "behavioral_signal_at": "{{behavioral_signal_at}}",
  "research_summary": "{{research_summary}}",
  "buying_trigger": "{{buying_trigger}}"
}
```

Use a Conditional Run so the HTTP API action fires only when the minimum identity requirement is met and the enrichment stage is complete.

## 8. Test sequence

1. Use a 3-5 row test table, not a production list.
2. Verify the domain Formula outputs the expected canonical domain.
3. Run one Waterfall and inspect which provider wins.
4. Force a missing-result row and confirm fallback behavior.
5. Run Claygent on one row and inspect sources/confidence.
6. Test the HTTP API action against the n8n test webhook.
7. Send the same row twice and confirm downstream idempotency behavior.
8. Change a freshness date to stale and confirm the Conditional Run becomes eligible.
9. Save the stable sequence as a Function after validation.

## Security

Do not place secrets in table formulas, exported screenshots, README files, or committed workflow JSON. Use Clay/n8n secret or account configuration and keep provider credentials outside the repository.
