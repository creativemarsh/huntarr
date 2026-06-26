from __future__ import annotations

import re
import time
from datetime import datetime
from html.parser import HTMLParser

import pandas as pd
import requests

_BASE = "https://www.getonbrd.com/api/v0"
_HEADERS = {"Accept": "application/json", "User-Agent": "huntarr/1.0"}

_CATEGORY_MAP: list[tuple[list[str], list[str]]] = [
    (["data", "analytics", "analytic", "bi ", "tableau", "power bi", "sql"], ["data-science-analytics"]),
    (["machine learning", "ml ", " ml", "deep learning", "nlp", "ia ", " ia", "inteligencia artificial"], ["machine-learning-ai"]),
    (["devops", "cloud", "aws", "azure", "gcp", "infra", "sre ", "sysadmin", "kubernetes", "docker"], ["sysadmin-devops-qa"]),
    (["mobile", "android", "ios", "flutter", "react native", "swift", "kotlin"], ["mobile-developer"]),
    (["cybersec", "security", "pentest", "seguridad"], ["cybersecurity"]),
]
_DEFAULT_CATEGORY = "programming"

_company_cache: dict[int, str] = {}


def _categories_for(term: str) -> list[str]:
    lower = term.lower()
    cats: list[str] = []
    for keywords, categories in _CATEGORY_MAP:
        if any(k in lower for k in keywords):
            cats.extend(categories)
    if not cats:
        cats.append(_DEFAULT_CATEGORY)
    return list(dict.fromkeys(cats))


def _strip_html(text: str) -> str:
    class _P(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.parts: list[str] = []

        def handle_data(self, data: str) -> None:
            self.parts.append(data)

    p = _P()
    p.feed(text or "")
    return " ".join(p.parts).strip()


def _company_name(company_id: int) -> str:
    if company_id in _company_cache:
        return _company_cache[company_id]
    try:
        r = requests.get(f"{_BASE}/companies/{company_id}", headers=_HEADERS, timeout=5)
        if r.status_code == 200:
            name = r.json()["data"]["attributes"]["name"]
            _company_cache[company_id] = name
            return name
    except Exception:
        pass
    _company_cache[company_id] = ""
    return ""


def scrape(term: str, results: int, ubicacion: str) -> pd.DataFrame:
    categories = _categories_for(term)
    per_cat = max(10, results // len(categories))
    term_words = [w for w in re.split(r"\W+", term.lower()) if len(w) > 2]

    rows: list[dict] = []
    seen: set[str] = set()

    for cat in categories:
        try:
            r = requests.get(
                f"{_BASE}/categories/{cat}/jobs",
                params={"per_page": per_cat, "page": 1},
                headers=_HEADERS,
                timeout=15,
            )
            r.raise_for_status()
        except Exception:
            continue

        for item in r.json().get("data", []):
            if item.get("type") != "job":
                continue
            attrs = item.get("attributes", {})
            job_id = item.get("id", "")
            if not job_id or job_id in seen:
                continue

            title = attrs.get("title", "")
            title_lower = title.lower()
            if term_words and not any(w in title_lower for w in term_words):
                continue

            seen.add(job_id)

            company_id = attrs.get("company", {}).get("data", {}).get("id")
            company = _company_name(int(company_id)) if company_id else ""

            pub = attrs.get("published_at")
            try:
                date_posted = datetime.fromtimestamp(pub).date().isoformat() if pub else None
            except Exception:
                date_posted = None

            modality = attrs.get("modality", "")
            is_remote = modality == "remote" or bool(attrs.get("remote", False))

            countries = attrs.get("countries", [])
            loc = ubicacion
            if countries:
                loc = countries[0] if isinstance(countries[0], str) else ubicacion

            rows.append({
                "job_url": f"https://www.getonbrd.com/jobs/{job_id}",
                "title": title,
                "company": company,
                "location": loc,
                "description": _strip_html(attrs.get("description", "")),
                "date_posted": date_posted,
                "is_remote": is_remote,
                "min_amount": attrs.get("min_salary"),
                "max_amount": attrs.get("max_salary"),
                "site": "getonboard",
            })

        if len(rows) >= results:
            break
        time.sleep(0.5)

    return pd.DataFrame(rows[:results]) if rows else pd.DataFrame()
