import { ArrowDownAZ } from "lucide-react";
import type { SortField } from "../types/listing";

const SORT_OPTIONS: { value: SortField; label: string }[] = [
  { value: "deal_score", label: "Best Deal" },
  { value: "price_asc", label: "Price: Low → High" },
  { value: "price_desc", label: "Price: High → Low" },
  { value: "mileage", label: "Lowest Mileage" },
  { value: "year", label: "Newest First" },
  { value: "distance", label: "Nearest First" },
];

interface Props {
  sort: SortField;
  onSort: (s: SortField) => void;
  total: number;
  sourceFilter: string;
  sources: string[];
  onSourceFilter: (s: string) => void;
}

export function SortBar({ sort, onSort, total, sourceFilter, sources, onSourceFilter }: Props) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 py-3">
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-400">
          <span className="text-white font-semibold">{total}</span> listings
        </span>

        {sources.length > 1 && (
          <select
            value={sourceFilter}
            onChange={(e) => onSourceFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white"
          >
            <option value="all">All Sources</option>
            {sources.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        )}
      </div>

      {/* Mobile: select dropdown */}
      <div className="sm:hidden flex items-center gap-2">
        <ArrowDownAZ className="w-4 h-4 text-gray-500 shrink-0" />
        <select
          value={sort}
          onChange={(e) => onSort(e.target.value as SortField)}
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* Desktop: button bar */}
      <div className="hidden sm:flex items-center gap-2">
        <ArrowDownAZ className="w-4 h-4 text-gray-500" />
        <div className="flex bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          {SORT_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              onClick={() => onSort(opt.value)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                sort === opt.value
                  ? "bg-blue-600 text-white"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
