import CvPanel from "./CvPanel";

async function getCvStatus() {
  try {
    const res = await fetch("http://localhost:8000/api/cv/status", {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function CvPage() {
  const status = await getCvStatus();

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100">Mi CV</h1>
        <p className="text-zinc-400 mt-1 text-sm">
          Sube tu CV base y extrae tu perfil para el pipeline.
        </p>
      </div>
      <CvPanel initialStatus={status} />
    </div>
  );
}
