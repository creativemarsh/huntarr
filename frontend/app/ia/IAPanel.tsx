'use client'

import { useState, useEffect, useRef, useMemo } from "react";

type ScoredJob = {
  id: string;
  titulo: string;
  empresa: string;
  ubicacion: string;
  url: string;
  descripcion: string;
  es_remoto: boolean;
  score: number;
  razon: string;
  scored_at: string;
};

type Filter = "all" | "top" | "relevant";

function scoreBadge(score: number) {
  if (score >= 80) return "bg-emerald-500/15 text-emerald-400 border-emerald-500/30";
  if (score >= 60) return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
  if (score >= 40) return "bg-orange-500/15 text-orange-400 border-orange-500/30";
  return "bg-zinc-800 text-zinc-500 border-zinc-700";
}

function scoreLabel(score: number) {
  if (score >= 80) return "Muy relevante";
  if (score >= 60) return "Relevante";
  if (score >= 40) return "Poco relevante";
  return "No relevante";
}

export default function IAPanel() {
  const [results, setResults]         = useState<ScoredJob[]>([]);
  const [running, setRunning]         = useState(false);
  const [currentJob, setCurrentJob]   = useState("");
  const [progress, setProgress]       = useState<{ current: number; total: number } | null>(null);
  const [error, setError]             = useState<string | null>(null);
  const [filter, setFilter]           = useState<Filter>("all");
  const [loading, setLoading]         = useState(true);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    loadResults();
    fetch("http://localhost:8000/api/ia/status")
      .then(r => r.json())
      .then(s => { if (s.running) { setRunning(true); connectSSE(); } })
      .catch(() => {});
  }, []);

  async function loadResults() {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/ia/results");
      const data = await res.json();
      setResults(data);
    } catch {}
    setLoading(false);
  }

  function connectSSE() {
    if (esRef.current) esRef.current.close();
    const es = new EventSource("http://localhost:8000/api/ia/events");
    esRef.current = es;

    es.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "scored") {
        setResults(prev => {
          const exists = prev.find(r => r.id === msg.result.id);
          const updated = exists
            ? prev.map(r => r.id === msg.result.id ? msg.result : r)
            : [...prev, msg.result];
          return updated.sort((a, b) => b.score - a.score);
        });
      } else if (msg.type === "progress") {
        setCurrentJob(msg.titulo);
        setProgress({ current: msg.current, total: msg.total });
      } else if (msg.type === "done") {
        setRunning(false);
        setCurrentJob("");
        loadResults();
        es.close();
      } else if (msg.type === "error") {
        setError(msg.message);
        setRunning(false);
        es.close();
      }
    };

    es.onerror = () => { setRunning(false); es.close(); };
  }

  async function handleClear() {
    try {
      await fetch("http://localhost:8000/api/ia/scores", { method: "DELETE" });
      setResults([]);
    } catch {}
  }

  async function handleScore() {
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/ia/score", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Error al iniciar");
      setRunning(true);
      setProgress(null);
      connectSSE();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al iniciar scoring");
    }
  }

  const filtered = useMemo(() => {
    if (filter === "top") return results.filter(r => r.score >= 80);
    if (filter === "relevant") return results.filter(r => r.score >= 60);
    return results;
  }, [results, filter]);

  const counts = useMemo(() => ({
    top: results.filter(r => r.score >= 80).length,
    relevant: results.filter(r => r.score >= 60).length,
    all: results.length,
  }), [results]);

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h2 className="text-sm font-semibold text-zinc-200">Calificación de ofertas</h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              {loading
                ? "Cargando..."
                : results.length === 0
                  ? "Sin resultados. Califica las ofertas scrapeadas."
                  : `${results.length} oferta(s) calificadas`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {!running && results.length > 0 && (
              <button
                onClick={handleClear}
                className="px-3 py-2 rounded-lg text-xs font-medium text-zinc-500 hover:text-red-400 hover:bg-zinc-800 transition-colors"
              >
                Limpiar
              </button>
            )}
            <button
              onClick={handleScore}
              disabled={running}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                running
                  ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                  : "bg-violet-600 hover:bg-violet-500 text-white"
              }`}
            >
              {running ? "Calificando..." : results.length > 0 ? "Re-calificar" : "Calificar ofertas"}
            </button>
          </div>
        </div>

        {running && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs text-zinc-400">
              <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-pulse" />
              {currentJob
                ? <span>Evaluando: <span className="text-zinc-200 font-mono truncate">{currentJob}</span></span>
                : "Iniciando..."}
            </div>
            {progress && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs text-zinc-500">
                  <span>{progress.current} / {progress.total}</span>
                  <span>{Math.round((progress.current / progress.total) * 100)}%</span>
                </div>
                <div className="h-1 bg-zinc-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-violet-500 rounded-full transition-all duration-300"
                    style={{ width: `${(progress.current / progress.total) * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {error && <p className="text-xs text-red-400 mt-2">✗ {error}</p>}
      </div>

      {/* Filtro tabs */}
      {results.length > 0 && (
        <div className="flex gap-2">
          {(["all", "relevant", "top"] as Filter[]).map(f => {
            const labels = { all: "Todas", relevant: "Relevantes", top: "Top" };
            const countMap = { all: counts.all, relevant: counts.relevant, top: counts.top };
            const active = filter === f;
            return (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
                  active
                    ? "bg-violet-600/20 text-violet-300 border border-violet-500/30"
                    : "bg-zinc-900 text-zinc-400 border border-zinc-800 hover:text-zinc-200"
                }`}
              >
                {labels[f]}
                <span className={`px-1.5 py-0.5 rounded text-xs ${active ? "bg-violet-500/30" : "bg-zinc-800"}`}>
                  {countMap[f]}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Lista */}
      {!loading && filtered.length > 0 ? (
        <div className="space-y-3">
          {filtered.map(job => <ScoredJobCard key={job.id} job={job} />)}
        </div>
      ) : !loading && results.length > 0 ? (
        <p className="text-sm text-zinc-500 text-center py-10">
          Sin ofertas para el filtro seleccionado.
        </p>
      ) : null}

    </div>
  );
}

function ScoredJobCard({ job }: { job: ScoredJob }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <a
              href={job.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-zinc-100 hover:text-violet-400 transition-colors line-clamp-1"
            >
              {job.titulo}
            </a>
            <span className={`shrink-0 px-2 py-0.5 rounded-md text-xs font-semibold border ${scoreBadge(job.score)}`}>
              {job.score} · {scoreLabel(job.score)}
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-0.5">
            {job.empresa}
            {job.ubicacion && job.ubicacion !== "nan" && (
              <span className="text-zinc-600"> · {job.ubicacion.split(",")[0].trim()}</span>
            )}
            {job.es_remoto && <span className="text-emerald-600 ml-1">· Remoto</span>}
          </p>
          {job.razon && (
            <p className="text-xs text-zinc-500 mt-1 italic">{job.razon}</p>
          )}
        </div>
        <button
          onClick={() => setExpanded(!expanded)}
          className="shrink-0 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {expanded ? "Menos" : "Ver más"}
        </button>
      </div>

      {expanded && job.descripcion && (
        <p className="text-xs text-zinc-400 leading-relaxed border-t border-zinc-800 pt-2 whitespace-pre-line line-clamp-10">
          {job.descripcion}
        </p>
      )}
    </div>
  );
}
