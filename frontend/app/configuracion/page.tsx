import ConfigForm from "./ConfigForm";
import SearchConfigForm from "./SearchConfigForm";

async function getConfig() {
  try {
    const res = await fetch("http://localhost:8000/api/config", { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

async function getSearchConfig() {
  try {
    const res = await fetch("http://localhost:8000/api/search/config", { cache: "no-store" });
    if (!res.ok) return null;
    return res.json();
  } catch { return null; }
}

export default async function ConfiguracionPage() {
  const [config, searchConfig] = await Promise.all([getConfig(), getSearchConfig()]);

  return (
    <div className="max-w-2xl mx-auto px-6 py-10 space-y-12">

      <section>
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-100">Configuración</h1>
          <p className="text-zinc-400 mt-1 text-sm">Elige tu proveedor de IA y configura los modelos del pipeline.</p>
        </div>
        <ConfigForm initialConfig={config} />
      </section>

      <div className="border-t border-zinc-800" />

      <section>
        <div className="mb-8">
          <h2 className="text-xl font-bold text-zinc-100">Búsqueda</h2>
          <p className="text-zinc-400 mt-1 text-sm">Configura qué ofertas buscar y con qué parámetros.</p>
        </div>
        <SearchConfigForm initialConfig={searchConfig} />
      </section>

    </div>
  );
}
