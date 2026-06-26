from __future__ import annotations

import json
import time
from urllib.parse import quote_plus

import pandas as pd


def scrape(term: str, results: int, ubicacion: str) -> pd.DataFrame:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return pd.DataFrame()

    query = f"{term} empleos {ubicacion}"
    url = f"https://www.google.com/search?q={quote_plus(query)}&hl=es&gl=cl&ibp=htl;jobs"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                locale="es-CL",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/120.0.0.0 Safari/537.36",
            )
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            # Wait for jobs panel to populate
            page.wait_for_timeout(4_000)

            rows = page.evaluate(_EXTRACT_JS)
            browser.close()
    except Exception:
        return pd.DataFrame()

    if not rows:
        import os
        if os.getenv("GOB_DEBUG"):
            with open("google_debug.html", "w", encoding="utf-8") as f:
                try:
                    with sync_playwright() as p2:
                        b2 = p2.chromium.launch(headless=True)
                        pg2 = b2.new_context(locale="es-CL").new_page()
                        pg2.goto(url, wait_until="domcontentloaded", timeout=30_000)
                        pg2.wait_for_timeout(4_000)
                        f.write(pg2.content())
                        b2.close()
                except Exception:
                    pass
        return pd.DataFrame()

    clean: list[dict] = []
    for job in rows[:results]:
        title = job.get("title", "").strip()
        company = job.get("company", "").strip()
        location = job.get("location", "").strip() or ubicacion
        description = job.get("description", "").strip()
        job_url = job.get("url", "").strip()
        if not title or not job_url:
            continue
        clean.append({
            "job_url": job_url,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "date_posted": None,
            "is_remote": "remoto" in location.lower() or "remote" in location.lower(),
            "min_amount": None,
            "max_amount": None,
            "site": "google",
        })

    return pd.DataFrame(clean) if clean else pd.DataFrame()


_EXTRACT_JS = """
() => {
    const jobs = [];

    // Strategy 1: Google Jobs structured panel (ibp=htl;jobs)
    // Job cards are typically <li> with a heading and metadata
    const trySelectors = [
        'li.iFjolb',        // common Google Jobs card class
        'li[data-jk]',      // Indeed-like data attribute Google sometimes injects
        'div[data-jk]',
        '[jsname="GKvYPb"]', // job title container
    ];

    for (const sel of trySelectors) {
        const items = document.querySelectorAll(sel);
        if (items.length > 0) {
            items.forEach(item => {
                const headingEl = item.querySelector('[role="heading"], h2, h3, h4');
                const title = headingEl ? headingEl.textContent.trim() : '';
                if (!title) return;
                const allText = Array.from(item.querySelectorAll('span, div'))
                    .map(el => el.textContent.trim())
                    .filter(t => t && t !== title && t.length < 200);
                const company = allText[0] || '';
                const location = allText[1] || '';
                const description = allText.slice(2).join(' ').slice(0, 500);
                const link = item.querySelector('a[href]');
                const url = link ? link.href : window.location.href;
                jobs.push({ title, company, location, description, url });
            });
            if (jobs.length > 0) break;
        }
    }

    // Strategy 2: JSON-LD structured data (JobPosting schema)
    if (jobs.length === 0) {
        document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
            try {
                const data = JSON.parse(s.textContent);
                const items = Array.isArray(data) ? data : (data['@graph'] || [data]);
                items.forEach(item => {
                    if (item['@type'] !== 'JobPosting') return;
                    const url = item.url || item.sameAs || '';
                    jobs.push({
                        title: item.title || '',
                        company: (item.hiringOrganization || {}).name || '',
                        location: ((item.jobLocation || {}).address || {}).addressLocality || '',
                        description: (item.description || '').replace(/<[^>]+>/g, ' ').slice(0, 500),
                        url,
                    });
                });
            } catch(e) {}
        });
    }

    return jobs;
}
"""
