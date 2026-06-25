'use client'

import { useState, useEffect } from "react";

type Config = {
  proveedor: string;
  api_key_set: boolean;
  api_key_preview: string | null;
  modelo_filtro: string;
  modelo_escritura: string;
  ollama_base_url: string;
};

const DEFAULT_MODELS = {
  ollama:     { filtro: "deepseek-r1:8b", escritura: "phi3.5" },
  openrouter: { filtro: "openrouter/auto", escritura: "openrouter/auto" },
};

function ModelSelect({
  value,
  onChange,
  models,
  loading,
}: {
  value: string;
  onChange: (v: string) => void;
  models: string[];
  loading: boolean;
}) {
  return (
    <div className="relative">
      <select
        value={models.includes(value) ? value : "__custom__"}
        onChange={(e) => {
          if (e.target.value !== "__custom__") onChange(e.target.value);
        }}
        disabled={loading}
        className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 font-mono appearance-none focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors disabled:opacity-50"
      >
        {loading && <option value="__custom__">Cargando modelos...</option>}
        {!loading && models.length === 0 && (
          <option value="__custom__">Sin modelos instalados</option>
        )}
        {models.map((m) => (
          <option key={m} value={m}>{m}</option>
        ))}
        {!loading && models.length > 0 && !models.includes(value) && (
          <option value="__custom__">{value} (custom)</option>
        )}
      </select>
      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 text-xs">▼</span>
    </div>
  );
}

export default function ConfigForm({ initialConfig }: { initialConfig: Config | null }) {
  const [proveedor,       setProveedor]       = useState(initialConfig?.proveedor        ?? "ollama");
  const [apiKey,          setApiKey]          = useState("");
  const [showKey,         setShowKey]         = useState(false);
  const [apiKeySaved,     setApiKeySaved]     = useState(initialConfig?.api_key_set      ?? false);
  const [apiKeyPreview,   setApiKeyPreview]   = useState(initialConfig?.api_key_preview  ?? null as string | null);
  const [modeloFiltro,    setModeloFiltro]    = useState(initialConfig?.modelo_filtro    ?? DEFAULT_MODELS.ollama.filtro);
  const [modeloEscritura, setModeloEscritura] = useState(initialConfig?.modelo_escritura ?? DEFAULT_MODELS.ollama.escritura);
  const [ollamaUrl,       setOllamaUrl]       = useState(initialConfig?.ollama_base_url  ?? "http://localhost:11434");
  const [ollamaModels,    setOllamaModels]    = useState<string[]>([]);
  const [loadingModels,   setLoadingModels]   = useState(false);
  const [saving,          setSaving]          = useState(false);
  const [saveResult,      setSaveResult]      = useState<"ok" | "error" | null>(null);
  const [testing,         setTesting]         = useState(false);
  const [testResult,      setTestResult]      = useState<{ ok: boolean; message: string } | null>(null);

  const backendOffline = initialConfig === null;

  useEffect(() => {
    if (proveedor === "ollama") fetchOllamaModels();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [proveedor, ollamaUrl]);

  async function fetchOllamaModels() {
    setLoadingModels(true);
    try {
      const res = await fetch("http://localhost:8000/api/providers/ollama/models");
      if (!res.ok) throw new Error();
      const data = await res.json();
      setOllamaModels(data.models);
    } catch {
      setOllamaModels([]);
    } finally {
      setLoadingModels(false);
    }
  }

  function handleProveedorChange(p: string) {
    setProveedor(p);
    const d = DEFAULT_MODELS[p as keyof typeof DEFAULT_MODELS];
    setModeloFiltro(d.filtro);
    setModeloEscritura(d.escritura);
    setTestResult(null);
  }

  async function handleSave() {
    setSaving(true);
    setSaveResult(null);
    try {
      const body: Record<string, string> = {
        proveedor,
        modelo_filtro: modeloFiltro,
        modelo_escritura: modeloEscritura,
        ollama_base_url: ollamaUrl,
      };
      if (apiKey) body.api_key = apiKey;

      const res = await fetch("http://localhost:8000/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error();

      setSaveResult("ok");
      if (apiKey) {
        setApiKeySaved(true);
        setApiKeyPreview(`${apiKey.slice(0, 8)}...`);
        setApiKey("");
      }
    } catch {
      setSaveResult("error");
    } finally {
      setSaving(false);
      setTimeout(() => setSaveResult(null), 3000);
    }
  }

  async function handleTest() {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/config/test", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Error desconocido");
      setTestResult({ ok: true, message: `Conexión exitosa — "${data.response}"` });
    } catch (e) {
      setTestResult({ ok: false, message: e instanceof Error ? e.message : "No se pudo conectar" });
    } finally {
      setTesting(false);
    }
  }

  return (
    <div className="space-y-5">

      {backendOffline && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl px-4 py-3 text-amber-400 text-sm">
          ⚠️ Backend offline — inícialo con{" "}
          <code className="font-mono bg-amber-500/10 px-1.5 py-0.5 rounded text-amber-300">
            uvicorn api.main:app --reload
          </code>
        </div>
      )}

      {/* Proveedor */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Proveedor</h2>
        <div className="flex gap-2">
          {(["ollama", "openrouter"] as const).map((p) => (
            <button
              key={p}
              onClick={() => handleProveedorChange(p)}
              className={`flex-1 py-2.5 px-4 rounded-lg text-sm font-medium transition-all ${
                proveedor === p
                  ? "bg-violet-600 text-white shadow-lg shadow-violet-500/20"
                  : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200"
              }`}
            >
              {p === "ollama" ? "🖥️  Ollama (local)" : "☁️  OpenRouter (nube)"}
            </button>
          ))}
        </div>
        <p className="text-xs text-zinc-500">
          {proveedor === "ollama"
            ? "Corre los modelos en tu máquina. Requiere Ollama instalado y corriendo."
            : "Usa modelos en la nube a través de OpenRouter. Requiere API key."}
        </p>
      </section>

      {/* API Key / URL */}
      {proveedor === "openrouter" ? (
        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">API Key</h2>
          {apiKeySaved && (
            <div className="flex items-center gap-2 text-emerald-400 text-sm bg-emerald-500/10 border border-emerald-500/20 rounded-lg px-3 py-2">
              <span>✓</span>
              <span>Guardada — <span className="font-mono">{apiKeyPreview}</span></span>
            </div>
          )}
          <div className="relative">
            <input
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={apiKeySaved ? "Nueva key para reemplazar la actual..." : "sk-or-..."}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 pr-16 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500 hover:text-zinc-300 transition-colors"
            >
              {showKey ? "Ocultar" : "Ver"}
            </button>
          </div>
        </section>
      ) : (
        <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Ollama</h2>
          <div>
            <label className="text-xs text-zinc-500 block mb-1.5">URL base</label>
            <input
              type="text"
              value={ollamaUrl}
              onChange={(e) => setOllamaUrl(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 font-mono focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors"
            />
          </div>
        </section>
      )}

      {/* Modelos */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Modelos</h2>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-zinc-500 block mb-1.5">
              Filtro / Scoring
              <span className="text-zinc-600 ml-2">evalúa y puntúa cada oferta</span>
            </label>
            {proveedor === "ollama" ? (
              <ModelSelect
                value={modeloFiltro}
                onChange={setModeloFiltro}
                models={ollamaModels}
                loading={loadingModels}
              />
            ) : (
              <input
                type="text"
                value={modeloFiltro}
                onChange={(e) => setModeloFiltro(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 font-mono focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors"
              />
            )}
          </div>
          <div>
            <label className="text-xs text-zinc-500 block mb-1.5">
              Escritura
              <span className="text-zinc-600 ml-2">genera CV adaptado y carta de presentación</span>
            </label>
            {proveedor === "ollama" ? (
              <ModelSelect
                value={modeloEscritura}
                onChange={setModeloEscritura}
                models={ollamaModels}
                loading={loadingModels}
              />
            ) : (
              <input
                type="text"
                value={modeloEscritura}
                onChange={(e) => setModeloEscritura(e.target.value)}
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 font-mono focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors"
              />
            )}
          </div>
        </div>
      </section>

      {/* Acciones */}
      <div className="flex items-center gap-3 pt-1">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
        >
          {saving ? "Guardando..." : "Guardar configuración"}
        </button>
        <button
          onClick={handleTest}
          disabled={testing}
          className="px-5 py-2.5 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-50 disabled:cursor-not-allowed text-zinc-100 text-sm font-medium rounded-lg border border-zinc-700 transition-colors"
        >
          {testing ? "Probando..." : "Probar conexión"}
        </button>

        {saveResult === "ok" && (
          <span className="text-emerald-400 text-sm">✓ Guardado</span>
        )}
        {saveResult === "error" && (
          <span className="text-red-400 text-sm">✗ Error al guardar</span>
        )}
      </div>

      {testResult && (
        <div className={`rounded-xl px-4 py-3 text-sm border ${
          testResult.ok
            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
            : "bg-red-500/10 border-red-500/20 text-red-400"
        }`}>
          {testResult.ok ? "✓ " : "✗ "}{testResult.message}
        </div>
      )}

    </div>
  );
}
