import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  Cell,
} from "recharts";
import type { MarketAnalytics } from "../types/listing";

const DEAL_COLORS: Record<string, string> = {
  "Great Deal": "#10b981",
  "Good Deal": "#3b82f6",
  "Fair Deal": "#f59e0b",
  Overpriced: "#ef4444",
  Unknown: "#6b7280",
};

function fmtPrice(n: number) {
  if (n >= 1000) return "$" + (n / 1000).toFixed(0) + "k";
  return "$" + n;
}

export function AnalyticsCharts({ analytics }: { analytics: MarketAnalytics }) {
  if (analytics.total_listings === 0) return null;

  const histData = analytics.price_histogram.map((b) => ({
    range: `${fmtPrice(b.bin_start)}–${fmtPrice(b.bin_end)}`,
    count: b.count,
  }));

  const yearData = Object.entries(analytics.avg_price_by_year)
    .sort(([a], [b]) => parseInt(a) - parseInt(b))
    .map(([year, avg]) => ({ year, price: avg }));

  return (
    <div className="space-y-6">
      {/* Price Distribution */}
      {histData.length > 0 && (
        <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Price Distribution</h3>
          <div className="h-52 sm:h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={histData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="range"
                  tick={{ fontSize: 10, fill: "#9ca3af" }}
                  angle={-35}
                  textAnchor="end"
                  height={50}
                  interval={0}
                />
                <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} />
                <Tooltip
                  contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
                  labelStyle={{ color: "#fff" }}
                  itemStyle={{ color: "#60a5fa" }}
                />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Price vs Mileage Scatter */}
      {analytics.price_vs_mileage.length > 0 && (
        <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Price vs. Mileage</h3>
          <div className="h-60 sm:h-72">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="mileage"
                  name="Mileage"
                  tick={{ fontSize: 11, fill: "#9ca3af" }}
                  tickFormatter={(v: number) => (v / 1000).toFixed(0) + "k"}
                  label={{ value: "Mileage", position: "insideBottom", offset: -5, style: { fill: "#6b7280", fontSize: 11 } }}
                />
                <YAxis
                  dataKey="price"
                  name="Price"
                  tick={{ fontSize: 11, fill: "#9ca3af" }}
                  tickFormatter={(v: number) => fmtPrice(v)}
                  label={{ value: "Price", angle: -90, position: "insideLeft", style: { fill: "#6b7280", fontSize: 11 } }}
                />
                <Tooltip
                  contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
                  formatter={(value, name) =>
                    name === "Price" ? ["$" + Number(value).toLocaleString(), String(name)] : [Number(value).toLocaleString() + " mi", String(name)]
                  }
                  labelFormatter={() => ""}
                />
                <Scatter data={analytics.price_vs_mileage} shape="circle">
                  {analytics.price_vs_mileage.map((entry, i) => (
                    <Cell
                      key={i}
                      fill={DEAL_COLORS[entry.deal_rating] || "#6b7280"}
                      fillOpacity={0.7}
                      r={5}
                    />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-3 justify-center">
            {Object.entries(DEAL_COLORS).filter(([k]) => k !== "Unknown").map(([label, color]) => (
              <div key={label} className="flex items-center gap-1.5 text-xs text-gray-400">
                <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
                {label}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Price by Year */}
      {yearData.length > 1 && (
        <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Average Price by Year</h3>
          <div className="h-48 sm:h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={yearData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="year" tick={{ fontSize: 12, fill: "#9ca3af" }} />
                <YAxis tick={{ fontSize: 11, fill: "#9ca3af" }} tickFormatter={(v: number) => fmtPrice(v)} />
                <Tooltip
                  contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: 8 }}
                  formatter={(value) => ["$" + Number(value).toLocaleString(), "Avg Price"]}
                  labelStyle={{ color: "#fff" }}
                />
                <Bar dataKey="price" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}
