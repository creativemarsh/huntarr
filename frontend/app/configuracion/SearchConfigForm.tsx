'use client'

import { useState } from "react";

type SearchConfig = {
  terminos_auto: string[];
  terminos_usuario: string[];
  terminos_busqueda: string[];
  ubicacion: string;
  horas_atras: number;
  resultados_por_termino: number;
  modo_junior: boolean;
  modo_senior: boolean;
  modo_trainee: boolean;
  modo_graduate: boolean;
  modo_practicas: boolean;
};

export default function SearchConfigForm({ initialConfig }: { initialConfig: SearchConfig | null }) {
  const cfg = initialConfig ?? {
    terminos_auto: [], terminos_usuario: [], terminos_busqueda: [],
    ubicacion: "Chile", horas_atras: 168, resultados_por_termino: 25,
    modo_junior: false, modo_senior: false,
    modo_trainee: false, modo_graduate: false, modo_practicas: false,
  };

  const [terminosAuto,    ]              = useState<string[]>(cfg.terminos_auto ?? []);
  const [terminosUsuario, setTermUsr]    = useState<string[]>(cfg.terminos_usuario ?? []);
  const [ubicacion,       setUbicacion]  = useState(cfg.ubicacion);
  const [horasAtras,      setHorasAtras] = useState(cfg.horas_atras);
  const [resultados,      setResultados] = useState(cfg.resultados_por_termino);
  const [modoJunior,      setModoJunior]    = useState(cfg.modo_junior);
  const [modoSenior,      setModoSenior]    = useState(cfg.modo_senior);
  const [modoTrainee,     setModoTrainee]   = useState(cfg.modo_trainee);
  const [modoGraduate,    setModoGraduate]  = useState(cfg.modo_graduate);
  const [modoPracticas,   setModoPracticas] = useState(cfg.modo_practicas);
  const [newTerm,         setNewTerm]    = useState("");
  const [saving,          setSaving]     = useState(false);
  const [saveResult,      setSaveResult] = useState<"ok" | "error" | null>(null);

  const baseTerms = [...terminosAuto, ...terminosUsuario];
  const terminosExpandidos = Array.from(new Set([
    ...(modoJunior    ? baseTerms.map(t => `${t} junior`)    : []),
    ...(modoSenior    ? baseTerms.map(t => `${t} senior`)    : []),
    ...(modoTrainee   ? baseTerms.map(t => `${t} trainee`)   : []),
    ...(modoGraduate  ? baseTerms.flatMap(t => [`graduate program ${t}`, `programa de graduados ${t}`]) : []),
    ...(modoPracticas ? baseTerms.flatMap(t => [`${t} prácticas`, `${t} intern`]) : []),
  ])).sort();

  function addTerm() {
    const t = newTerm.trim().toLowerCase();
    if (!t || terminosUsuario.includes(t) || terminosAuto.includes(t)) return;
    setTermUsr([...terminosUsuario, t]);
    setNewTerm("");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") { e.preventDefault(); addTerm(); }
  }

  async function handleSave() {
    setSaving(true);
    setSaveResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/search/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          terminos_usuario: terminosUsuario,
          ubicacion,
          horas_atras: horasAtras,
          resultados_por_termino: resultados,
          modo_junior: modoJunior,
          modo_senior: modoSenior,
          modo_trainee: modoTrainee,
          modo_graduate: modoGraduate,
          modo_practicas: modoPracticas,
        }),
      });
      if (!res.ok) throw new Error();
      setSaveResult("ok");
    } catch {
      setSaveResult("error");
    } finally {
      setSaving(false);
      setTimeout(() => setSaveResult(null), 3000);
    }
  }

  const totalTerminos = terminosAuto.length + terminosUsuario.length;

  return (
    <div className="space-y-5">

      {/* Términos de búsqueda */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Términos de búsqueda</h2>
          {totalTerminos > 0 && (
            <span className="text-xs text-zinc-500">{totalTerminos} término(s)</span>
          )}
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            value={newTerm}
            onChange={e => setNewTerm(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Agregar término personalizado..."
            className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors"
          />
          <button
            onClick={addTerm}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 text-zinc-100 text-sm rounded-lg transition-colors"
          >
            Agregar
          </button>
        </div>

        {totalTerminos === 0 && terminosExpandidos.length === 0 && (
          <p className="text-xs text-zinc-600 italic">Sin términos — extrae tu perfil desde Mi CV para auto-poblar.</p>
        )}

        {terminosAuto.length > 0 && (
          <div>
            <p className="text-xs text-zinc-600 mb-1.5">Del perfil</p>
            <div className="flex flex-wrap gap-1.5">
              {terminosAuto.map(t => (
                <span key={t} className="px-2.5 py-1 bg-zinc-800/60 border border-zinc-700/50 text-zinc-500 rounded-lg text-xs">{t}</span>
              ))}
            </div>
          </div>
        )}

        {terminosUsuario.length > 0 && (
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <p className="text-xs text-zinc-600">Personalizados</p>
              <button onClick={() => setTermUsr([])} className="text-xs text-zinc-600 hover:text-red-400 transition-colors">Limpiar</button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {terminosUsuario.map(t => (
                <span key={t} className="flex items-center gap-1 px-2.5 py-1 bg-zinc-800 border border-zinc-700 text-zinc-300 rounded-lg text-xs">
                  {t}
                  <button onClick={() => setTermUsr(terminosUsuario.filter(x => x !== t))} className="text-zinc-500 hover:text-red-400 transition-colors ml-1">×</button>
                </span>
              ))}
            </div>
          </div>
        )}

        {terminosExpandidos.length > 0 && (
          <div>
            <p className="text-xs text-zinc-600 mb-1.5">Por programas activos</p>
            <div className="flex flex-wrap gap-1.5">
              {terminosExpandidos.map(t => (
                <span key={t} className="px-2.5 py-1 bg-violet-900/30 border border-violet-700/40 text-violet-400 rounded-lg text-xs">{t}</span>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Parámetros */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Parámetros</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-zinc-500 block mb-1.5">Ubicación</label>
            <input type="text" value={ubicacion} onChange={e => setUbicacion(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors" />
          </div>
          <div>
            <label className="text-xs text-zinc-500 block mb-1.5">Horas atrás</label>
            <input type="number" min={1} value={horasAtras} onChange={e => setHorasAtras(Number(e.target.value))}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors" />
          </div>
          <div>
            <label className="text-xs text-zinc-500 block mb-1.5">Resultados por término</label>
            <input type="number" min={1} value={resultados} onChange={e => setResultados(Number(e.target.value))}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2.5 text-sm text-zinc-100 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500/30 transition-colors" />
          </div>
        </div>
      </section>

      {/* Programas especiales */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Programas especiales</h2>
        <Toggle label="Junior" description='Agrega "[rol] Junior" a los términos de búsqueda' value={modoJunior} onChange={setModoJunior} />
        <Toggle label="Senior" description='Agrega "[rol] Senior" a los términos de búsqueda' value={modoSenior} onChange={setModoSenior} />
        <Toggle label="Trainee" description='Agrega "[rol] Trainee" a los términos de búsqueda' value={modoTrainee} onChange={setModoTrainee} />
        <Toggle label="Graduate Program" description='Agrega "Graduate Program [rol]" y "Programa de Graduados [rol]"' value={modoGraduate} onChange={setModoGraduate} />
        <Toggle label="Prácticas" description='Agrega "[rol] Prácticas" y "[rol] Intern"' value={modoPracticas} onChange={setModoPracticas} />
      </section>

      {/* Acciones */}
      <div className="flex items-center gap-3 pt-1">
        <button onClick={handleSave} disabled={saving}
          className="px-5 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors">
          {saving ? "Guardando..." : "Guardar búsqueda"}
        </button>
        {saveResult === "ok"    && <span className="text-emerald-400 text-sm">✓ Guardado</span>}
        {saveResult === "error" && <span className="text-red-400 text-sm">✗ Error al guardar</span>}
      </div>

    </div>
  );
}

function Toggle({ label, description, value, onChange }: {
  label: string; description: string; value: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-zinc-200">{label}</p>
        <p className="text-xs text-zinc-500 mt-0.5">{description}</p>
      </div>
      <button onClick={() => onChange(!value)}
        className={`relative shrink-0 w-11 h-6 rounded-full transition-colors ${value ? "bg-violet-600" : "bg-zinc-700"}`}>
        <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${value ? "translate-x-5" : "translate-x-0"}`} />
      </button>
    </div>
  );
}
