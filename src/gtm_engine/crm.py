from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from typing import Any

import requests

from .models import CRMPayloadBundle, ProspectRecord, RoutingDecision, ScoreBreakdown


def _iso(value: datetime | None = None) -> str:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _split_name(name: str | None) -> tuple[str, str]:
    if not name:
        return "", ""
    parts = name.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def build_hubspot_payloads(
    record: ProspectRecord,
    score: ScoreBreakdown,
    route: RoutingDecision,
    synced_at: datetime | None = None,
) -> CRMPayloadBundle:
    timestamp = _iso(synced_at)
    company_properties: dict[str, str] = {
        "name": record.company_name or record.domain or "Unknown company",
        "domain": record.domain or "",
        "industry": record.industry or "",
        "numberofemployees": str(record.employee_count or ""),
        "gtm_score": str(score.total),
        "gtm_tier": route.tier,
        "gtm_source": record.source or "unknown",
        "gtm_route_action": route.action,
        "gtm_route_owner": route.owner,
        "gtm_synced_at": timestamp,
    }
    company = {"properties": company_properties}

    contact: dict[str, Any] | None = None
    if record.email or record.person_name:
        first, last = _split_name(record.person_name)
        contact = {
            "properties": {
                "email": record.email or "",
                "firstname": first,
                "lastname": last,
                "jobtitle": record.title or "",
                "linkedin_url": record.linkedin_url or "",
                "gtm_score": str(score.total),
                "gtm_tier": route.tier,
                "gtm_source": record.source or "unknown",
                "gtm_synced_at": timestamp,
            }
        }

    association = None
    if contact is not None:
        association = {
            "from": "contact",
            "to": "company",
            "type": "contact_to_company",
            "strategy": "associate_after_upsert",
        }

    return CRMPayloadBundle(
        company=company,
        contact=contact,
        association=association,
        metadata={
            "score_breakdown": score.model_dump(),
            "routing": route.model_dump(),
            "synced_at": timestamp,
        },
    )


class MockCRMAdapter:
    """Offline-safe CRM sink that returns deterministic IDs for replay testing."""

    @staticmethod
    def _stable_id(prefix: str, value: str) -> str:
        digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"mock_{prefix}_{digest}"

    def upsert(self, bundle: CRMPayloadBundle) -> dict[str, Any]:
        company_props = bundle.company.get("properties", {})
        company_identity = company_props.get("domain") or company_props.get("name") or "unknown"
        company_id = self._stable_id("company", str(company_identity).lower())
        contact_id = None
        if bundle.contact:
            contact_props = bundle.contact.get("properties", {})
            contact_identity = contact_props.get("email") or (
                f"{contact_props.get('firstname', '')}|{contact_props.get('lastname', '')}|{company_id}"
            )
            contact_id = self._stable_id("contact", str(contact_identity).lower())
        return {
            "status": "mock_upserted",
            "company_id": company_id,
            "contact_id": contact_id,
            "associated": bool(contact_id),
        }


def should_retry_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code <= 599


class HubSpotCRMAdapter:
    """Small HubSpot REST adapter; not used by the default offline demo."""

    base_url = "https://api.hubapi.com"

    def __init__(
        self,
        access_token: str | None = None,
        *,
        session: requests.Session | None = None,
        max_attempts: int = 3,
    ) -> None:
        token = access_token if access_token is not None else os.getenv("HUBSPOT_ACCESS_TOKEN", "")
        if not token.strip():
            raise ValueError("HUBSPOT_ACCESS_TOKEN is required for real HubSpot sync")
        self.access_token = token.strip()
        self.session = session or requests.Session()
        self.max_attempts = max(1, max_attempts)

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        last_response: requests.Response | None = None
        for attempt in range(1, self.max_attempts + 1):
            response = self.session.request(
                method,
                f"{self.base_url}{path}",
                headers=self.headers,
                timeout=20,
                **kwargs,
            )
            last_response = response
            if not should_retry_status(response.status_code) or attempt == self.max_attempts:
                response.raise_for_status()
                return response
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(2 ** (attempt - 1), 4)
            time.sleep(delay)
        assert last_response is not None
        last_response.raise_for_status()
        return last_response

    def _search(self, object_type: str, property_name: str, value: str) -> str | None:
        response = self._request(
            "POST",
            f"/crm/v3/objects/{object_type}/search",
            json={
                "filterGroups": [
                    {"filters": [{"propertyName": property_name, "operator": "EQ", "value": value}]}
                ],
                "properties": [property_name],
                "limit": 1,
            },
        )
        results = response.json().get("results", [])
        return str(results[0]["id"]) if results else None

    def _upsert_object(
        self,
        object_type: str,
        payload: dict[str, Any],
        unique_property: str,
    ) -> str:
        properties = payload.get("properties", {})
        unique_value = str(properties.get(unique_property, "")).strip()
        if not unique_value:
            raise ValueError(f"{object_type} payload requires {unique_property} for idempotent upsert")
        existing_id = self._search(object_type, unique_property, unique_value)
        if existing_id:
            response = self._request(
                "PATCH",
                f"/crm/v3/objects/{object_type}/{existing_id}",
                json=payload,
            )
            return str(response.json()["id"])
        response = self._request("POST", f"/crm/v3/objects/{object_type}", json=payload)
        return str(response.json()["id"])

    def upsert(self, bundle: CRMPayloadBundle) -> dict[str, Any]:
        company_id = self._upsert_object("companies", bundle.company, "domain")
        contact_id = None
        if bundle.contact and bundle.contact.get("properties", {}).get("email"):
            contact_id = self._upsert_object("contacts", bundle.contact, "email")
        return {
            "status": "hubspot_upserted",
            "company_id": company_id,
            "contact_id": contact_id,
            "associated": False,
        }
