from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import pandas as pd


_TECH_ALIASES = {
    "hubspot crm": "hubspot",
    "hubspot": "hubspot",
    "salesforce crm": "salesforce",
    "google-workspace": "google workspace",
    "google workspace": "google workspace",
}


def normalize_domain(value: str | None) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().lower()
    if not text:
        return None
    candidate = text if "://" in text else f"https://{text}"
    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    return host or None


def normalize_technology(value: str) -> str:
    text = " ".join(str(value).strip().lower().split())
    return _TECH_ALIASES.get(text, text.replace("-", " "))


def _normalize_technologies(value: Any) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    if isinstance(value, list):
        items = value
    else:
        text = str(value).replace(",", ";")
        items = [part for part in text.split(";") if part.strip()]
    normalized = [normalize_technology(item) for item in items if str(item).strip()]
    return list(dict.fromkeys(normalized))


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    text_columns = [
        "company_name",
        "person_name",
        "title",
        "location",
        "industry",
        "email",
        "phone",
        "source",
    ]
    for column in text_columns:
        if column in out.columns:
            out[column] = out[column].map(
                lambda value: value.strip() if isinstance(value, str) else value
            )
    if "domain" in out.columns:
        out["domain"] = out["domain"].map(normalize_domain)
    if "technologies" in out.columns:
        out["technologies"] = out["technologies"].map(_normalize_technologies)
    return out
