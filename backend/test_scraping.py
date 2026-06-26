"""
Test rápido de cada fuente de scraping por separado.
Uso: python test_scraping.py [term] [location]
"""
import sys
import os

# Permite importar desde services/
sys.path.insert(0, os.path.dirname(__file__))

TERM = sys.argv[1] if len(sys.argv) > 1 else "data engineer"
LOCATION = sys.argv[2] if len(sys.argv) > 2 else "Chile"
N = 5

print(f"\n{'='*60}")
print(f"Término: {TERM!r}  |  Ubicación: {LOCATION!r}")
print(f"{'='*60}\n")


def show(source: str, df):
    if df is None or df.empty:
        print(f"[{source.upper():12s}]  0 resultados")
        return
    print(f"[{source.upper():12s}]  {len(df)} resultado(s)")
    for _, row in df.iterrows():
        url    = str(row.get("job_url", row.get("url", "")) or "")
        titulo = str(row.get("title", row.get("titulo", "")) or "").strip()
        emp    = str(row.get("company", row.get("empresa", "")) or "").strip()
        desc   = str(row.get("description", row.get("descripcion", "")) or "").strip()
        print(f"  • {titulo} — {emp}  ({len(desc)} chars)")
        if url:
            print(f"    {url[:90]}")
    # Descripción completa del primer resultado con descripción
    for _, row in df.iterrows():
        desc = str(row.get("description", row.get("descripcion", "")) or "").strip()
        if desc:
            titulo = str(row.get("title", row.get("titulo", "")) or "").strip()
            emp    = str(row.get("company", row.get("empresa", "")) or "").strip()
            print(f"\n  --- DESCRIPCIÓN COMPLETA: {titulo} — {emp} ---")
            print(f"  {desc[:1000]}")
            break
    print()


# ── Indeed + LinkedIn (JobSpy) ──────────────────────────────────────────────
try:
    from jobspy import scrape_jobs
    df_jobspy = scrape_jobs(
        site_name=["indeed", "linkedin"],
        search_term=f'"{TERM}"',
        location=LOCATION,
        hours_old=168,
        results_wanted=N,
        country_indeed="Chile",
        linkedin_fetch_description=True,
    )
    # Normalize column names
    if "job_url" not in df_jobspy.columns and "url" in df_jobspy.columns:
        df_jobspy = df_jobspy.rename(columns={"url": "job_url"})
except Exception as e:
    print(f"[JOBSPY ERR] {e}")
    df_jobspy = None

show("indeed+linkedin", df_jobspy)

# ── GetOnBoard ──────────────────────────────────────────────────────────────
try:
    from services.scraper.getonboard import scrape as gob_scrape
    df_gob = gob_scrape(TERM, N, LOCATION)
except Exception as e:
    print(f"[GETONBOARD ERR] {e}")
    df_gob = None

show("getonboard", df_gob)

# ── FirstJob ────────────────────────────────────────────────────────────────
try:
    from services.scraper.firstjob import scrape as fj_scrape
    df_fj = fj_scrape(TERM, N, LOCATION)
except Exception as e:
    print(f"[FIRSTJOB ERR] {e}")
    df_fj = None

show("firstjob", df_fj)

