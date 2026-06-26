import Link from "next/link";

const SERVICE_PATTERNS = [
  "429", "503", "502", "500",
  "peticiones", "límite", "limite",
  "no está disponible", "no se pudo conectar",
  "configuración", "configuracion",
  "rate limit", "too many",
];

export function isServiceError(message: string): boolean {
  const lower = message.toLowerCase();
  return SERVICE_PATTERNS.some(p => lower.includes(p));
}

export default function ServiceErrorHint({ message }: { message: string }) {
  if (!isServiceError(message)) return null;
  return (
    <Link
      href="/configuracion"
      className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors mt-1"
    >
      → Cambiar modelo en Configuración
    </Link>
  );
}
