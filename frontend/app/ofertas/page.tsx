'use client'

import { useState } from "react";
import ScrapingEnVivo from "./ScrapingEnVivo";
import HistorialOfertas from "./HistorialOfertas";

export default function PostulacionesPage() {
  const [historialKey, setHistorialKey] = useState(0);

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-10">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Postulaciones</h1>
        <p className="text-zinc-400 mt-1 text-sm">Gestiona tus ofertas y postulaciones.</p>
      </div>

      <ScrapingEnVivo onDone={() => setHistorialKey(k => k + 1)} />

      <div className="border-t border-zinc-800" />

      <HistorialOfertas key={historialKey} />
    </div>
  );
}
