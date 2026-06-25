from jobspy import scrape_jobs
df = scrape_jobs(site_name=["google"], search_term="data engineer", location="Santiago, Chile", results_wanted=5)
print(f"Filas: {len(df)}, Columnas: {list(df.columns)}")
if not df.empty:
    print(df[["title","company","site"]].to_string())
