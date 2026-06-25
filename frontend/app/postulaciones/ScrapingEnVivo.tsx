'use client'

import { useState, useEffect, useRef } from "react";

type Job = {
  id: string;
  titulo: string;
  empresa: string;
  ubicacion: string;
  url: string;
  descripcion: string;
  es_remoto: boolean;
};

interface Props {
  onDone: () => void;
}

export default function ScrapingEnVivo({ onDone }: Props) {
  const [jobs, setJobs]               = useState<Job[]>([]);
  const [running, setRunning]         = useState(false);
  const [currentTerm, setCurrentTerm] = useState("");
  const [error, setError]             = useState<string | null>(null);
  const [total, setTotal]             = useState<number | null>(null);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/scraper/status")
      .then(r => r.json())
      .then(s => { if (s.running) { setRunning(true); connectSSE(); } })
      .catch(() => {});
  }, []);

  function connectSSE() {
    if (esRef.current) esRef.current.close();
    const es = new EventSource("http://localhost:8000/api/scraper/events");
    esRef.current = es;

    es.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "job") {
        setJobs(prev => prev.find(j => j.id === msg.job.id) ? prev : [msg.job, ...prev]);
      } else if (msg.type === "progress") {
        setCurrentTerm(msg.term);
      } else if (msg.type === "done") {
        setRunning(false);
        setCurrentTerm("");
        setTotal(msg.total ?? null);
        onDone();
        es.close();
      } else if (msg.type === "error") {
        setError(msg.message);
        setRunning(false);
        es.close();
      }
    };

    es.onerror = () => { setRunning(false); es.close(); };
  }

  async function handleStart() {
    setError(null);
    setJobs([]);
    setTotal(null);
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
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-zinc-200">Scraping en vivo</h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            {running
              ? `${jobs.length} oferta(s) encontrada(s) hasta ahora`
              : total !== null
                ? `Completado — ${total} oferta(s) nuevas encontradas`
                : "Inicia un scraping para buscar ofertas"}
          </p>
        </div>
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

      {running && (
        <div className="flex items-center gap-2 text-xs text-zinc-400">
          <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-pulse" />
          {currentTerm
            ? <>Buscando: <span className="text-zinc-200 font-mono">{currentTerm}</span></>
            : "Iniciando..."}
        </div>
      )}

      {error && <p className="text-xs text-red-400">✗ {error}</p>}

      {jobs.length > 0 && (
        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {jobs.map(job => (
            <div key={job.id} className="flex items-start gap-3 py-2 border-t border-zinc-800 first:border-0">
              <div className="min-w-0 flex-1">
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-medium text-zinc-200 hover:text-violet-400 transition-colors line-clamp-1"
                >
                  {job.titulo}
                </a>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {job.empresa}
                  {job.ubicacion && job.ubicacion !== "nan" && (
                    <span> · {job.ubicacion.split(",")[0].trim()}</span>
                  )}
                  {job.es_remoto && <span className="text-emerald-600 ml-1">· Remoto</span>}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
