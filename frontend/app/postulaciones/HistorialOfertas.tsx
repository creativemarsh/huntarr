'use client'

import { useState, useEffect, useMemo } from "react";

type Job = {
  id: string;
  titulo: string;
  empresa: string;
  ubicacion: string;
  url: string;
  descripcion: string;
  fecha_scrape: string;
  fecha_publicacion?: string | null;
  es_remoto: boolean;
  salario_min: number | null;
  salario_max: number | null;
};

type Recency = "all" | "1d" | "3d" | "7d" | "14d" | "30d";

const RECENCY_OPTIONS: { value: Recency; label: string; days: number }[] = [
  { value: "1d",  label: "Hoy",              days: 1  },
  { value: "3d",  label: "Últimos 3 días",   days: 3  },
  { value: "7d",  label: "Última semana",    days: 7  },
  { value: "14d", label: "Últimas 2 semanas",days: 14 },
  { value: "30d", label: "Último mes",       days: 30 },
];

export default function HistorialOfertas() {
  const [allJobs, setAllJobs]               = useState<Job[]>([]);
  const [loading, setLoading]               = useState(true);
  const [search, setSearch]                 = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [recency, setRecency]               = useState<Recency>("all");

  useEffect(() => { loadJobs(); }, []);

  async function loadJobs() {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/scraper/jobs");
      const data = await res.json();
      setAllJobs(data);
    } catch {}
    setLoading(false);
  }

  async function handleClear() {
    try {
      await fetch("http://localhost:8000/api/scraper/jobs", { method: "DELETE" });
      setAllJobs([]);
    } catch {}
  }

  const cities = useMemo(() => {
    const set = new Set<string>();
    allJobs.forEach(j => {
      const city = j.ubicacion?.split(",")[0]?.trim();
      if (city && city !== "nan" && city !== "undefined") set.add(city);
    });
    return Array.from(set).sort();
  }, [allJobs]);

  const filteredJobs = useMemo(() => {
    let jobs = allJobs;

    if (search.trim()) {
      const q = search.trim().toLowerCase();
      jobs = jobs.filter(j => j.titulo.toLowerCase().includes(q));
    }

    if (locationFilter) {
      jobs = jobs.filter(j =>
        j.ubicacion?.toLowerCase().includes(locationFilter.toLowerCase())
      );
    }

    if (recency !== "all") {
      const days = RECENCY_OPTIONS.find(o => o.value === recency)!.days;
      const cutoff = Date.now() - days * 86_400_000;
      jobs = jobs.filter(j => {
        const dateStr = j.fecha_publicacion ?? j.fecha_scrape;
        if (!dateStr) return true;
        return new Date(dateStr).getTime() >= cutoff;
      });
    }

    return jobs;
  }, [allJobs, search, locationFilter, recency]);

  const hasFilters = search.trim() !== "" || locationFilter !== "" || recency !== "all";

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-200">Historial de ofertas</h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            {loading
              ? "Cargando..."
              : allJobs.length === 0
                ? "Sin ofertas guardadas"
                : hasFilters
                  ? `${filteredJobs.length} de ${allJobs.length} oferta(s)`
                  : `${allJobs.length} oferta(s) en total`}
          </p>
        </div>
        {!loading && allJobs.length > 0 && (
          <button
            onClick={handleClear}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-zinc-500 hover:text-red-400 hover:bg-zinc-800 transition-colors"
          >
            Limpiar historial
          </button>
        )}
      </div>

      {/* Filtros */}
      {allJobs.length > 0 && (
        <div className="flex gap-3 flex-wrap">
          <input
            type="text"
            placeholder="Buscar por título..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="flex-1 min-w-[180px] bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-zinc-600"
          />
          <select
            value={locationFilter}
            onChange={e => setLocationFilter(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-400 focus:outline-none focus:border-zinc-600"
          >
            <option value="">Todas las ciudades</option>
            {cities.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <select
            value={recency}
            onChange={e => setRecency(e.target.value as Recency)}
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-400 focus:outline-none focus:border-zinc-600"
          >
            <option value="all">Cualquier fecha</option>
            {RECENCY_OPTIONS.map(o => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
          {hasFilters && (
            <button
              onClick={() => { setSearch(""); setLocationFilter(""); setRecency("all"); }}
              className="px-3 py-2 rounded-lg text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              Limpiar filtros
            </button>
          )}
        </div>
      )}

      {/* Lista */}
      {loading ? null : filteredJobs.length > 0 ? (
        <div className="space-y-3">
          {filteredJobs.map(job => <JobCard key={job.id} job={job} />)}
        </div>
      ) : allJobs.length > 0 ? (
        <p className="text-sm text-zinc-500 text-center py-10">
          Sin resultados para los filtros aplicados.
        </p>
      ) : (
        <p className="text-sm text-zinc-500 text-center py-10">
          Todavía no hay ofertas guardadas.
        </p>
      )}
    </div>
  );
}

function JobCard({ job }: { job: Job }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-zinc-100 hover:text-violet-400 transition-colors line-clamp-1"
          >
            {job.titulo}
          </a>
          <p className="text-xs text-zinc-400 mt-0.5">
            {job.empresa}
            {job.ubicacion && job.ubicacion !== "nan" && (
              <span className="text-zinc-600"> · {job.ubicacion.split(",")[0].trim()}</span>
            )}
            {job.es_remoto && <span className="text-emerald-600 ml-1">· Remoto</span>}
          </p>
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="shrink-0 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {expanded ? "Menos" : "Ver más"}
        </button>
      </div>

      {expanded && job.descripcion && (
        <p className="text-xs text-zinc-400 leading-relaxed border-t border-zinc-800 pt-2 whitespace-pre-line line-clamp-6">
          {job.descripcion}
        </p>
      )}
    </div>
  );
}
