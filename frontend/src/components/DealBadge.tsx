import type { DealRating } from "../types/listing";

const CONFIG: Record<DealRating, { bg: string; text: string; label: string }> = {
  "Great Deal": { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "Great Deal" },
  "Good Deal": { bg: "bg-blue-500/20", text: "text-blue-400", label: "Good Deal" },
  "Fair Deal": { bg: "bg-amber-500/20", text: "text-amber-400", label: "Fair Deal" },
  Overpriced: { bg: "bg-red-500/20", text: "text-red-400", label: "Overpriced" },
  Unknown: { bg: "bg-gray-500/20", text: "text-gray-400", label: "—" },
};

export function DealBadge({ rating, score }: { rating: DealRating; score: number }) {
  const c = CONFIG[rating] ?? CONFIG.Unknown;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
      {c.label}
      <span className="opacity-70">{score.toFixed(0)}</span>
    </span>
  );
}
