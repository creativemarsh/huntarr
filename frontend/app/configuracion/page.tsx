import ConfigForm from "./ConfigForm";

async function getConfig() {
  try {
    const res = await fetch("http://localhost:8000/api/config", {
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default async function ConfiguracionPage() {
  const config = await getConfig();

  return (
    <div className="max-w-2xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100">Configuración</h1>
        <p className="text-zinc-400 mt-1 text-sm">
          Elige tu proveedor de IA y configura los modelos del pipeline.
        </p>
      </div>
      <ConfigForm initialConfig={config} />
    </div>
  );
}
