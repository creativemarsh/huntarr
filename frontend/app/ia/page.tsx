import IAPanel from "./IAPanel";

export default function IAPage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-zinc-100">IA</h1>
        <p className="text-zinc-400 mt-1 text-sm">Califica automáticamente las ofertas según tu perfil.</p>
      </div>
      <IAPanel />
    </div>
  );
}
