import OfertasScrapeadas from "./OfertasScrapeadas";

export default function PostulacionesPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100">Postulaciones</h1>
        <p className="text-zinc-400 mt-1 text-sm">Gestiona tus ofertas y postulaciones.</p>
      </div>
      <OfertasScrapeadas />
    </div>
  );
}
