from __future__ import annotations

import re
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

_BASE = "https://www.firstjob.me"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "es-CL,es;q=0.9",
}


def scrape(term: str, results: int, ubicacion: str) -> pd.DataFrame:
    try:
        r = requests.get(
            f"{_BASE}/ofertas",
            params={"q": term},
            headers=_HEADERS,
            timeout=15,
        )
        r.raise_for_status()
    except Exception:
        return pd.DataFrame()

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select(".card-job")

    term_words = [w for w in re.split(r"\W+", term.lower()) if len(w) > 2]

    rows: list[dict] = []
    for card in cards:
        link_el = card.select_one("a[href]")
        if not link_el:
            continue
        href = link_el.get("href", "")
        job_url = href if href.startswith("http") else f"{_BASE}{href}"

        title_el = card.select_one(".card-job-top--info-heading")
        company_el = card.select_one(".card-job-top--company")
        location_el = card.select_one(".card-job-top--location")
        desc_el = card.select_one(".card-job-description")

        title = title_el.get_text(strip=True) if title_el else ""
        company = company_el.get_text(strip=True) if company_el else ""
        location = location_el.get_text(strip=True) if location_el else ubicacion
        description = desc_el.get_text(strip=True) if desc_el else ""

        combined = (title + " " + description).lower()
        if term_words and not any(w in combined for w in term_words):
            continue

        if len(rows) >= results:
            break

        rows.append({
            "job_url": job_url,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "date_posted": None,
            "is_remote": False,
            "min_amount": None,
            "max_amount": None,
            "site": "firstjob",
        })

    return pd.DataFrame(rows) if rows else pd.DataFrame()
