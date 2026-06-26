'use client'

import { useRef, useState, useEffect } from "react";
import ServiceErrorHint from "../components/ServiceErrorHint";

type Profile = {
  nombre: string;
  cargo_objetivo: string[];
  skills: string[];
  educacion: string;
  experiencia_anos: number;
  idiomas: string[];
  resumen: string;
  ubicacion: string;
};

type CvStatus = {
  cv_uploaded: boolean;
  profile_extracted: boolean;
  profile: Profile | null;
};

export default function CvPanel({ initialStatus }: { initialStatus: CvStatus | null }) {
  const [status, setStatus]       = useState<CvStatus>(initialStatus ?? { cv_uploaded: false, profile_extracted: false, profile: null });
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [uploadResult, setUploadResult]   = useState<{ ok: boolean; message: string } | null>(null);
  const [extractResult, setExtractResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [modelInfo, setModelInfo] = useState<{ proveedor: string; modelo: string } | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch("http://localhost:8000/api/config")
      .then(r => r.json())
      .then(d => setModelInfo({ proveedor: d.proveedor, modelo: d.modelo_escritura }))
      .catch(() => {});
  }, []);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadResult(null);
    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/cv/upload", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Error al subir");
      setStatus(s => ({ ...s, cv_uploaded: true, profile_extracted: false, profile: null }));
      setUploadResult({ ok: true, message: "CV subido correctamente" });
    } catch (e) {
      setUploadResult({ ok: false, message: e instanceof Error ? e.message : "Error al subir" });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function handleExtract() {
    setExtracting(true);
    setExtractResult(null);
    try {
      const res = await fetch("http://localhost:8000/api/cv/extract", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Error al extraer");
      setStatus(s => ({ ...s, profile_extracted: true, profile: data.profile }));
      setExtractResult({ ok: true, message: "Perfil extraído correctamente" });
    } catch (e) {
      setExtractResult({ ok: false, message: e instanceof Error ? e.message : "Error al extraer" });
    } finally {
      setExtracting(false);
    }
  }

  return (
    <div className="space-y-6">

      {/* Upload */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">CV Base</h2>

        {status.cv_uploaded && (
          <p className="text-sm text-emerald-400">✓ CV subido</p>
        )}

        <div className="flex items-center gap-3">
          <input
            ref={fileRef}
            type="file"
            accept=".pdf"
            onChange={handleUpload}
            className="hidden"
            id="cv-upload"
          />
          <label
            htmlFor="cv-upload"
            className={`cursor-pointer px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              uploading
                ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                : "bg-zinc-800 text-zinc-100 hover:bg-zinc-700 border border-zinc-700"
            }`}
          >
            {uploading ? "Subiendo..." : status.cv_uploaded ? "Reemplazar CV" : "Subir CV (PDF)"}
          </label>
        </div>

        {uploadResult && (
          <p className={`text-sm ${uploadResult.ok ? "text-emerald-400" : "text-red-400"}`}>
            {uploadResult.ok ? "✓" : "✗"} {uploadResult.message}
          </p>
        )}
      </section>

      {/* Extract */}
      <section className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Perfil Extraído</h2>
          {modelInfo && (
            <span className="text-xs text-zinc-600">
              {modelInfo.proveedor} · <span className="font-mono">{modelInfo.modelo}</span>
            </span>
          )}
        </div>

        {status.profile_extracted && (
          <p className="text-sm text-emerald-400">✓ Perfil extraído</p>
        )}

        <button
          onClick={handleExtract}
          disabled={!status.cv_uploaded || extracting}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            !status.cv_uploaded || extracting
              ? "bg-zinc-700 text-zinc-500 cursor-not-allowed"
              : "bg-violet-600 text-white hover:bg-violet-500"
          }`}
        >
          {extracting ? "Extrayendo..." : status.profile_extracted ? "Re-extraer perfil" : "Extraer perfil"}
        </button>

        {extractResult && (
          <div>
            <p className={`text-sm ${extractResult.ok ? "text-emerald-400" : "text-red-400"}`}>
              {extractResult.ok ? "✓" : "✗"} {extractResult.message}
            </p>
            {!extractResult.ok && <ServiceErrorHint message={extractResult.message} />}
          </div>
        )}

        {status.profile && (
          <ProfileViewer
            profile={status.profile}
            onSave={(updated) => setStatus(s => ({ ...s, profile: updated }))}
          />
        )}
      </section>

    </div>
  );
}

function ProfileViewer({ profile, onSave }: { profile: Profile; onSave: (p: Profile) => void }) {
  const [editing, setEditing]   = useState(false);
  const [saving, setSaving]     = useState(false);
  const [saveMsg, setSaveMsg]   = useState<string | null>(null);
  const [draft, setDraft]       = useState<Profile>(profile);

  function startEdit() { setDraft(profile); setEditing(true); setSaveMsg(null); }
  function cancelEdit() { setEditing(false); setSaveMsg(null); }

  async function handleSave() {
    setSaving(true);
    setSaveMsg(null);
    try {
      const res = await fetch("http://localhost:8000/api/cv/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail ?? "Error al guardar");
      onSave(data.profile);
      setEditing(false);
      setSaveMsg("Perfil actualizado correctamente");
    } catch (e) {
      setSaveMsg(e instanceof Error ? e.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  function setList(field: keyof Profile, raw: string) {
    setDraft(d => ({ ...d, [field]: raw.split(",").map(s => s.trim()).filter(Boolean) }));
  }

  if (!editing) {
    return (
      <div className="mt-4 border-t border-zinc-800 pt-4 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-zinc-500">Perfil extraído</span>
          <button onClick={startEdit} className="text-xs text-zinc-500 hover:text-violet-400 transition-colors">
            Editar
          </button>
        </div>
        <ProfileField label="Nombre" value={profile.nombre} />
        {profile.ubicacion && <ProfileField label="Ubicación" value={profile.ubicacion} />}
        <ProfileField label="Resumen" value={profile.resumen} />
        <ProfileField label="Educación" value={profile.educacion} />
        <ProfileField label="Experiencia" value={`${profile.experiencia_anos} año(s)`} />
        <ProfileListField label="Cargos objetivo" items={profile.cargo_objetivo} />
        <ProfileListField label="Skills" items={profile.skills} />
        <ProfileListField label="Idiomas" items={profile.idiomas} />
        {saveMsg && <p className="text-xs text-emerald-400">{saveMsg}</p>}
      </div>
    );
  }

  return (
    <div className="mt-4 border-t border-zinc-800 pt-4 space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs text-zinc-500">Editando perfil</span>
        <div className="flex gap-2">
          <button onClick={cancelEdit} className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors">
            Cancelar
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-1 rounded-lg text-xs font-medium bg-violet-600 hover:bg-violet-500 text-white disabled:opacity-50 transition-colors"
          >
            {saving ? "Guardando..." : "Guardar"}
          </button>
        </div>
      </div>

      <EditField label="Nombre" value={draft.nombre} onChange={v => setDraft(d => ({ ...d, nombre: v }))} />
      <EditField label="Ubicación" value={draft.ubicacion} onChange={v => setDraft(d => ({ ...d, ubicacion: v }))} />
      <EditField label="Educación" value={draft.educacion} onChange={v => setDraft(d => ({ ...d, educacion: v }))} />
      <EditField label="Experiencia (años)" value={String(draft.experiencia_anos)} onChange={v => setDraft(d => ({ ...d, experiencia_anos: parseInt(v) || 0 }))} type="number" />
      <EditArea label="Resumen" value={draft.resumen} onChange={v => setDraft(d => ({ ...d, resumen: v }))} />
      <EditField label="Cargos objetivo (separados por coma)" value={draft.cargo_objetivo.join(", ")} onChange={v => setList("cargo_objetivo", v)} />
      <EditField label="Skills (separadas por coma)" value={draft.skills.join(", ")} onChange={v => setList("skills", v)} />
      <EditField label="Idiomas (separados por coma)" value={draft.idiomas.join(", ")} onChange={v => setList("idiomas", v)} />

      {saveMsg && <p className="text-xs text-red-400">{saveMsg}</p>}
    </div>
  );
}

function EditField({ label, value, onChange, type = "text" }: { label: string; value: string; onChange: (v: string) => void; type?: string }) {
  return (
    <div>
      <p className="text-xs text-zinc-500 mb-1">{label}</p>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-500"
      />
    </div>
  );
}

function EditArea({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div>
      <p className="text-xs text-zinc-500 mb-1">{label}</p>
      <textarea
        value={value}
        onChange={e => onChange(e.target.value)}
        rows={3}
        className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-500 resize-none"
      />
    </div>
  );
}

function ProfileField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-zinc-500 mb-1">{label}</p>
      <p className="text-sm text-zinc-200">{value}</p>
    </div>
  );
}

function ProfileListField({ label, items }: { label: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <p className="text-xs text-zinc-500 mb-1">{label}</p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={`${item}-${i}`} className="px-2 py-0.5 bg-zinc-800 text-zinc-300 rounded text-xs">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
