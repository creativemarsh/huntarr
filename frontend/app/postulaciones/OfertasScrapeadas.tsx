'use client'

import { useState, useEffect, useRef } from "react";

type Job = {
  id: string;
  titulo: string;
  empresa: string;
  ubicacion: string;
  url: string;
  descripcion: string;
  fecha_scrape: string;
  es_remoto: boolean;
  fuente: string;
  salario_min: number | null;
  salario_max: number | null;
};

export default function OfertasScrapeadas() {
  const [jobs,        setJobs]        = useState<Job[]>([]);
  const [running,     setRunning]     = useState(false);
  const [done,        setDone]        = useState(false);
  const [currentTerm, setCurrentTerm] = useState("");
  const [error,       setError]       = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/scraper/status")
      .then(r => r.json())
      .then(s => {
        if (s.running) {
          setRunning(true);
          connectSSE();
        }
      })
      .catch(() => {});
  }, []);

  function connectSSE() {
    if (esRef.current) esRef.current.close();
    const es = new EventSource("http://localhost:8000/api/scraper/events");
    esRef.current = es;

    es.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "job") {
        setJobs(prev => {
          if (prev.find(j => j.id === msg.job.id)) return prev;
          return [msg.job, ...prev];
        });
      } else if (msg.type === "progress") {
        setCurrentTerm(msg.term);
      } else if (msg.type === "done") {
        setRunning(false);
        setDone(true);
        setCurrentTerm("");
        es.close();
      } else if (msg.type === "error") {
        setError(msg.message);
        setRunning(false);
        es.close();
      }
    };

    es.onerror = () => {
      setRunning(false);
      es.close();
    };
  }

  async function handleClear() {
    try {
      await fetch("http://localhost:8000/api/scraper/jobs", { method: "DELETE" });
      setJobs([]);
      setDone(false);
      setError(null);
    } catch {
      setError("Error al limpiar historial");
    }
  }

  async function handleStart() {
    setError(null);
    setDone(false);
    setJobs([]);
    try {
      const res = await fetch("http://localhost:8000/api/scraper/start", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Error al iniciar");
      setRunning(true);
      connectSSE();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al iniciar scraping");
    }
  }

  return (
    <div className="space-y-6">

      {/* Header sección */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-zinc-200">Ofertas scrapeadas</h2>
            {jobs.length > 0 && (
              <p className="text-xs text-zinc-500 mt-0.5">{jobs.length} oferta(s) encontrada(s)</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!running && jobs.length > 0 && (
              <button
                onClick={handleClear}
                className="px-3 py-2 rounded-lg text-sm font-medium text-zinc-400 hover:text-red-400 hover:bg-zinc-800 transition-colors"
              >
                Limpiar
              </button>
            )}
            <button
              onClick={handleStart}
              disabled={running}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                running
                  ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                  : "bg-violet-600 hover:bg-violet-500 text-white"
              }`}
            >
              {running ? "Scrapeando..." : "Iniciar scraping"}
            </button>
          </div>
        </div>

        {running && (
          <div className="flex items-center gap-2 text-xs text-zinc-400">
            <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-pulse" />
            {currentTerm ? <>Buscando: <span className="text-zinc-200 font-mono">{currentTerm}</span></> : "Iniciando..."}
          </div>
        )}
        {done && !running && (
          <p className="text-xs text-emerald-400">✓ Scraping completado — {jobs.length} oferta(s) encontradas</p>
        )}
        {error && (
          <p className="text-xs text-red-400">✗ {error}</p>
        )}
      </div>

      {/* Lista de ofertas */}
      {jobs.length > 0 && (
        <div className="space-y-3">
          {jobs.map(job => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
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
            {job.ubicacion && <span className="text-zinc-600"> · {job.ubicacion}</span>}
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
