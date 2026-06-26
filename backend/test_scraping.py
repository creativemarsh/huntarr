from jobspy import scrape_jobs

# Queries siguiendo el formato exacto de la documentación
queries = [
    "data engineer jobs near Santiago, Chile in the last week",
    "data engineer jobs near Chile in the last week",
    "data engineer jobs near Santiago in the last week",
    "software engineer jobs near Santiago, Chile in the last week",
    "data engineer jobs near London, United Kingdom in the last week",  # control: ciudad conocida
]

for q in queries:
    try:
        df = scrape_jobs(
            site_name="google",
            google_search_term=q,
            results_wanted=5,
        )
        print(f"[{len(df):2d}] {q}")
    except Exception as e:
        print(f"[ERR] {q} — {e}")

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
