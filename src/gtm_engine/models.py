from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _normalize_domain_input(value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip().lower()
    if not text:
        return None
    candidate = text if "://" in text else f"https://{text}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


class ProspectRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    company_name: str | None = None
    domain: str | None = None
    person_name: str | None = None
    title: str | None = None
    linkedin_url: str | None = None
    location: str | None = None
    industry: str | None = None
    employee_count: int | None = None
    company_stage: str | None = None
    technologies: list[str] = Field(default_factory=list)
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    source_record_id: str | None = None
    enrichment_confidence: float | None = None
    firmographic_fit: float = 0.0
    technographic_fit: float = 0.0
    hiring_signal: float = 0.0
    funding_signal: float = 0.0
    intent_signal: float = 0.0
    behavioral_signal: float = 0.0
    hiring_signal_at: datetime | None = None
    funding_signal_at: datetime | None = None
    intent_signal_at: datetime | None = None
    behavioral_signal_at: datetime | None = None
    research_summary: str | None = None
    buying_trigger: str | None = None

    @field_validator("domain", mode="before")
    @classmethod
    def normalize_domain(cls, value: str | None) -> str | None:
        return _normalize_domain_input(value)

    @field_validator("company_name", "person_name", "title", "industry", mode="before")
    @classmethod
    def strip_text(cls, value: Any) -> Any:
        return value.strip() if isinstance(value, str) else value

    @field_validator(
        "firmographic_fit",
        "technographic_fit",
        "hiring_signal",
        "funding_signal",
        "intent_signal",
        "behavioral_signal",
        mode="before",
    )
    @classmethod
    def clamp_signal(cls, value: Any) -> float:
        if value is None or value == "":
            return 0.0
        number = float(value)
        return max(0.0, min(1.0, number))

    @model_validator(mode="after")
    def require_company_identity(self) -> "ProspectRecord":
        if not self.company_name and not self.domain:
            raise ValueError("company identity requires company_name or domain")
        return self


class ScoreBreakdown(BaseModel):
    total: int = Field(ge=0, le=100)
    components: dict[str, int]
    reasons: list[str] = Field(default_factory=list)


class RoutingDecision(BaseModel):
    tier: str
    action: str
    owner: str


class CRMPayloadBundle(BaseModel):
    company: dict[str, Any]
    contact: dict[str, Any] | None = None
    association: dict[str, Any] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
