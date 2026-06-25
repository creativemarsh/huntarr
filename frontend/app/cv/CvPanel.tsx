'use client'

import { useRef, useState } from "react";

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
  const fileRef = useRef<HTMLInputElement>(null);

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
        <h2 className="text-xs font-semibold text-zinc-400 uppercase tracking-widest">Perfil Extraído</h2>

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
          <p className={`text-sm ${extractResult.ok ? "text-emerald-400" : "text-red-400"}`}>
            {extractResult.ok ? "✓" : "✗"} {extractResult.message}
          </p>
        )}

        {status.profile && (
          <div className="mt-4 space-y-3 border-t border-zinc-800 pt-4">
            <ProfileField label="Nombre" value={status.profile.nombre} />
            {status.profile.ubicacion && <ProfileField label="Ubicación" value={status.profile.ubicacion} />}
            <ProfileField label="Resumen" value={status.profile.resumen} />
            <ProfileField label="Educación" value={status.profile.educacion} />
            <ProfileField label="Experiencia" value={`${status.profile.experiencia_anos} año(s)`} />
            <ProfileListField label="Cargos objetivo" items={status.profile.cargo_objetivo} />
            <ProfileListField label="Skills" items={status.profile.skills} />
            <ProfileListField label="Idiomas" items={status.profile.idiomas} />
          </div>
        )}
      </section>

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
        {items.map(item => (
          <span key={item} className="px-2 py-0.5 bg-zinc-800 text-zinc-300 rounded text-xs">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
