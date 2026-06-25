'use client'

import Link from "next/link";
import { usePathname } from "next/navigation";

const nav = [
  { href: "/configuracion", label: "Configuración", icon: "⚙️" },
  { href: "/dashboard",     label: "Dashboard",     icon: "📊", disabled: true },
  { href: "/cv",            label: "Mi CV",          icon: "📄" },
  { href: "/postulaciones", label: "Postulaciones",  icon: "💼" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 sticky top-0 h-screen bg-zinc-900 border-r border-zinc-800 flex flex-col">
      <div className="px-4 py-5 border-b border-zinc-800">
        <span className="text-violet-400 font-bold text-lg tracking-tight">
          🎯 Huntarr
        </span>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {nav.map(({ href, label, icon, disabled }) => {
          if (disabled) {
            return (
              <span
                key={href}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-zinc-600 cursor-not-allowed select-none"
              >
                <span>{icon}</span>
                <span>{label}</span>
              </span>
            );
          }
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-violet-600/20 text-violet-300"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
              }`}
            >
              <span>{icon}</span>
              <span>{label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-zinc-800">
        <p className="text-xs text-zinc-600 px-3">v0.1.0</p>
      </div>
    </aside>
  );
}
