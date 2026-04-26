import { useState, useMemo, useEffect } from "react";
import { Search as SearchIcon, BarChart3, LayoutGrid, Loader2, AlertCircle } from "lucide-react";
import { useSearch } from "./hooks/useSearch";
import { SearchBar } from "./components/SearchBar";
import { ListingCard } from "./components/ListingCard";
import { MarketOverview } from "./components/MarketOverview";
import { AnalyticsCharts } from "./components/Analytics";
import { SortBar } from "./components/SortBar";
import type { Listing, SortField } from "./types/listing";
import "./App.css";

function sortListings(listings: Listing[], sort: SortField): Listing[] {
  const sorted = [...listings];
  switch (sort) {
    case "deal_score":
      return sorted.sort((a, b) => b.deal_score - a.deal_score);
    case "price_asc":
      return sorted.sort((a, b) => a.price - b.price);
    case "price_desc":
      return sorted.sort((a, b) => b.price - a.price);
    case "mileage":
      return sorted.sort((a, b) => a.mileage - b.mileage);
    case "year":
      return sorted.sort((a, b) => b.year - a.year);
    default:
      return sorted;
  }
}

type Tab = "listings" | "analytics";

export default function App() {
  const { params, data, loading, error, search } = useSearch();
  const [sort, setSort] = useState<SortField>("deal_score");
  const [sourceFilter, setSourceFilter] = useState("all");
  const [tab, setTab] = useState<Tab>("listings");

  // Auto-search on mount
  useEffect(() => {
    search();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredListings = useMemo(() => {
    if (!data) return [];
    let filtered = data.listings;
    if (sourceFilter !== "all") {
      filtered = filtered.filter((l) => l.source === sourceFilter);
    }
    return sortListings(filtered, sort);
  }, [data, sort, sourceFilter]);

  const sources = useMemo(() => {
    if (!data) return [];
    return [...new Set(data.listings.map((l) => l.source))];
  }, [data]);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 py-3 sm:py-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
              <SearchIcon className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                Auto<span className="text-blue-400">Scout</span>
              </h1>
              <p className="text-xs text-gray-500">Every listing. Every source. Best deal.</p>
            </div>
          </div>
          <SearchBar params={params} loading={loading} onSearch={search} />
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6">
        {/* Loading state */}
        {loading && !data && (
          <div className="flex flex-col items-center justify-center py-32">
            <Loader2 className="w-10 h-10 text-blue-500 animate-spin mb-4" />
            <p className="text-gray-400">
              Scanning CarGurus, Cars.com, AutoTrader, Carvana, CarMax…
            </p>
            <p className="text-xs text-gray-600 mt-1">This takes a few seconds</p>
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="flex items-center gap-3 bg-red-500/10 border border-red-500/30 rounded-xl p-4 mb-6">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <div>
              <p className="text-sm text-red-400 font-medium">Search failed</p>
              <p className="text-xs text-red-400/70">{error}</p>
            </div>
          </div>
        )}

        {/* Results */}
        {data && (
          <>
            {/* Tabs */}
            <div className="flex items-center gap-1 bg-gray-800/50 p-1 rounded-lg w-fit mb-6">
              <button
                onClick={() => setTab("listings")}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  tab === "listings" ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"
                }`}
              >
                <LayoutGrid className="w-4 h-4" />
                Listings
              </button>
              <button
                onClick={() => setTab("analytics")}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  tab === "analytics" ? "bg-gray-700 text-white" : "text-gray-400 hover:text-white"
                }`}
              >
                <BarChart3 className="w-4 h-4" />
                Analytics
              </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 sm:gap-6">
              {/* Sidebar — on mobile this shows first */}
              <aside className="lg:col-span-1 space-y-4 order-1 lg:order-1">
                <MarketOverview
                  analytics={data.analytics}
                  sourcesSucceeded={data.sources_succeeded}
                  sourcesFailed={data.sources_failed}
                />
              </aside>

              {/* Main content */}
              <div className="lg:col-span-3 order-2 lg:order-2">
                {tab === "listings" && (
                  <>
                    <SortBar
                      sort={sort}
                      onSort={setSort}
                      total={filteredListings.length}
                      sourceFilter={sourceFilter}
                      sources={sources}
                      onSourceFilter={setSourceFilter}
                    />

                    {loading && (
                      <div className="flex items-center gap-2 text-sm text-blue-400 mb-4">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Refreshing results…
                      </div>
                    )}

                    {filteredListings.length === 0 && !loading && (
                      <div className="text-center py-20">
                        <p className="text-gray-400">No listings found</p>
                        <p className="text-xs text-gray-600 mt-1">
                          Try adjusting your search or filters
                        </p>
                      </div>
                    )}

                    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3 sm:gap-4">
                      {filteredListings.map((listing) => (
                        <ListingCard key={listing.id} listing={listing} />
                      ))}
                    </div>
                  </>
                )}

                {tab === "analytics" && (
                  <AnalyticsCharts analytics={data.analytics} />
                )}
              </div>
            </div>
          </>
        )}

        {/* Empty state (before first search) */}
        {!data && !loading && !error && (
          <div className="flex flex-col items-center justify-center py-32 text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 flex items-center justify-center mb-4">
              <SearchIcon className="w-8 h-8 text-blue-400" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">
              Search the entire car market
            </h2>
            <p className="text-sm text-gray-400 max-w-md">
              AutoScout aggregates listings from CarGurus, Cars.com, AutoTrader, Carvana,
              and CarMax to find you the best deal.
            </p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 mt-12 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center text-xs text-gray-600">
          AutoScout aggregates publicly available listings. Prices and availability may change.
          Always verify with the seller.
        </div>
      </footer>
    </div>
  );
}
