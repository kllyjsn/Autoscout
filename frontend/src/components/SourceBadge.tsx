import type { Source } from "../types/listing";

const COLORS: Record<Source, string> = {
  CarGurus: "bg-violet-500/20 text-violet-300",
  "Cars.com": "bg-sky-500/20 text-sky-300",
  AutoTrader: "bg-orange-500/20 text-orange-300",
  Carvana: "bg-cyan-500/20 text-cyan-300",
  CarMax: "bg-yellow-500/20 text-yellow-300",
  "Facebook Marketplace": "bg-blue-500/20 text-blue-300",
  Craigslist: "bg-purple-500/20 text-purple-300",
  TrueCar: "bg-teal-500/20 text-teal-300",
  Edmunds: "bg-rose-500/20 text-rose-300",
};

export function SourceBadge({ source }: { source: Source }) {
  const cls = COLORS[source] ?? "bg-gray-500/20 text-gray-300";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${cls}`}>
      {source}
    </span>
  );
}
