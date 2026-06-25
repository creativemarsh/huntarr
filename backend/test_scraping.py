from jobspy import scrape_jobs

df = scrape_jobs(
    site_name=["indeed", "linkedin"],
    search_term='"data engineer"',
    location="Chile",
    hours_old=168,
    results_wanted=10,
    country_indeed="Chile",
    linkedin_fetch_description=True,
)

print(f"{len(df)} resultado(s)\n")

shown = {"indeed": False, "linkedin": False}

for _, row in df.iterrows():
    titulo  = str(row.get("title", "")).strip()
    empresa = str(row.get("company", "")).strip()
    fuente  = str(row.get("site", "")).strip()
    desc    = str(row.get("description", "") or "").strip()
    nivel   = str(row.get("job_level", "") or "").strip()
    nivel_str = f" | nivel: {nivel}" if nivel and nivel != "nan" else ""
    print(f"[{fuente}] {titulo} — {empresa}  ({len(desc)} chars{nivel_str})")

print("\n" + "="*60)
print("DESCRIPCIÓN COMPLETA — una por fuente")
print("="*60)

for _, row in df.iterrows():
    fuente = str(row.get("site", "")).strip()
    desc   = str(row.get("description", "") or "").strip()
    if not shown.get(fuente) and desc:
        titulo  = str(row.get("title", "")).strip()
        empresa = str(row.get("company", "")).strip()
        print(f"\n--- [{fuente.upper()}] {titulo} — {empresa} ---\n")
        print(desc)
        shown[fuente] = True
    if all(shown.values()):
        break
