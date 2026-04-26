import { TrendingDown, TrendingUp, BarChart3, Car } from "lucide-react";
import type { MarketAnalytics } from "../types/listing";

function fmtPrice(n: number) {
  return "$" + n.toLocaleString("en-US");
}

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

export function MarketOverview({
  analytics,
  sourcesSucceeded,
  sourcesFailed,
}: {
  analytics: MarketAnalytics;
  sourcesSucceeded: string[];
  sourcesFailed: string[];
}) {
  const stats = [
    {
      label: "Total Listings",
      value: fmt(analytics.total_listings),
      icon: Car,
      color: "text-blue-400",
    },
    {
      label: "Median Price",
      value: fmtPrice(analytics.median_price),
      icon: BarChart3,
      color: "text-emerald-400",
    },
    {
      label: "Lowest Price",
      value: fmtPrice(analytics.min_price),
      icon: TrendingDown,
      color: "text-green-400",
    },
    {
      label: "Highest Price",
      value: fmtPrice(analytics.max_price),
      icon: TrendingUp,
      color: "text-red-400",
    },
  ];

  return (
    <div className="space-y-4">
      {/* Stats cards */}
      <div className="grid grid-cols-2 gap-2 sm:gap-3">
        {stats.map((s) => (
          <div
            key={s.label}
            className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-3 sm:p-4"
          >
            <div className="flex items-center gap-1.5 sm:gap-2 mb-1">
              <s.icon className={`w-3.5 sm:w-4 h-3.5 sm:h-4 ${s.color}`} />
              <span className="text-[10px] sm:text-xs text-gray-400">{s.label}</span>
            </div>
            <p className="text-base sm:text-xl font-bold text-white">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Deal breakdown */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Deal Breakdown</h3>
        <div className="flex gap-3">
          <DealCount label="Great" count={analytics.great_deals_count} color="bg-emerald-500" total={analytics.total_listings} />
          <DealCount label="Good" count={analytics.good_deals_count} color="bg-blue-500" total={analytics.total_listings} />
          <DealCount label="Fair" count={analytics.fair_deals_count} color="bg-amber-500" total={analytics.total_listings} />
          <DealCount label="Over" count={analytics.overpriced_count} color="bg-red-500" total={analytics.total_listings} />
        </div>
      </div>

      {/* Source status */}
      <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Sources</h3>
        <div className="flex flex-wrap gap-2">
          {sourcesSucceeded.map((s) => (
            <span key={s} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-emerald-500/15 text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              {s}
              {analytics.listings_by_source[s] != null && (
                <span className="opacity-60">({analytics.listings_by_source[s]})</span>
              )}
            </span>
          ))}
          {sourcesFailed.map((s) => (
            <span key={s} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs bg-red-500/15 text-red-400">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Avg price by source */}
      {Object.keys(analytics.avg_price_by_source).length > 0 && (
        <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-3">Average Price by Source</h3>
          <div className="space-y-2">
            {Object.entries(analytics.avg_price_by_source)
              .sort(([, a], [, b]) => a - b)
              .map(([source, avg]) => {
                const pct = analytics.max_price > 0 ? (avg / analytics.max_price) * 100 : 0;
                return (
                  <div key={source}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-400">{source}</span>
                      <span className="text-white font-medium">{fmtPrice(avg)}</span>
                    </div>
                    <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 rounded-full transition-all" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}

function DealCount({ label, count, color, total }: { label: string; count: number; color: string; total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="flex-1 text-center">
      <div className="text-lg font-bold text-white">{count}</div>
      <div className="text-[10px] text-gray-400 mb-1">{label}</div>
      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
