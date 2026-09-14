# CRM Mapping

The reference output is compatible with HubSpot CRM v3 object payloads. The project keeps mapping separate from scoring so CRM changes do not rewrite qualification logic.

## Company object

| Engine field | CRM property | Notes |
|---|---|---|
| company_name | name | canonical display name |
| domain | domain | company dedupe/search key |
| industry | industry | normalized if available |
| employee_count | numberofemployees | standard-like numeric field |
| score.total | gtm_score | custom property |
| routing.tier | gtm_tier | custom property |
| source | gtm_source | custom attribution property |
| routing.action | gtm_route_action | custom property |
| routing.owner | gtm_route_owner | logical queue/owner mapping |
| sync timestamp | gtm_synced_at | last engine write |

## Contact object

| Engine field | CRM property |
|---|---|
| email | email |
| person_name first token | firstname |
| remaining name | lastname |
| title | jobtitle |
| linkedin_url | linkedin_url |
| score.total | gtm_score |
| routing.tier | gtm_tier |
| source | gtm_source |
| sync timestamp | gtm_synced_at |

## Upsert strategy

1. Search company by normalized `domain`.
2. PATCH if found, POST if not found.
3. Search contact by normalized `email` when email exists.
4. PATCH if found, POST if not found.
5. Associate contact to company after both IDs are known.
6. Persist the workflow idempotency key in an audit/event layer so a replay cannot create a second commercial action.

The included `HubSpotCRMAdapter` implements the search/create/update boundary and retries HTTP 429/5xx responses. The default demo uses `MockCRMAdapter` and never makes a network call.

## Bidirectional sync design

For a real deployment, CRM-to-engine events should be handled as a separate inbound event type rather than silently overwriting enrichment data. Recommended fields on inbound CRM events:

- crm_object_id
- crm_updated_at
- changed_properties
- owner/stage changes
- lifecycle state

Conflict rule: explicit sales/user-entered ownership and lifecycle fields win over enrichment automation unless a documented business rule says otherwise.
