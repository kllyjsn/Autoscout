import { useState } from "react";
import { Search, SlidersHorizontal, X } from "lucide-react";
import type { SearchParams } from "../types/listing";

interface Props {
  params: SearchParams;
  loading: boolean;
  onSearch: (params: Partial<SearchParams>) => void;
}

const POPULAR_SEARCHES = [
  { make: "Rivian", model: "R1S", label: "Rivian R1S" },
  { make: "Tesla", model: "Model Y", label: "Tesla Model Y" },
  { make: "Toyota", model: "Camry", label: "Toyota Camry" },
  { make: "Honda", model: "Civic", label: "Honda Civic" },
  { make: "Ford", model: "F-150", label: "Ford F-150" },
  { make: "BMW", model: "3 Series", label: "BMW 3 Series" },
  { make: "Toyota", model: "RAV4", label: "Toyota RAV4" },
  { make: "Porsche", model: "911", label: "Porsche 911" },
  { make: "Chevrolet", model: "Corvette", label: "Chevy Corvette" },
  { make: "Jeep", model: "Wrangler", label: "Jeep Wrangler" },
];

export function SearchBar({ params, loading, onSearch }: Props) {
  const [showFilters, setShowFilters] = useState(false);
  const [make, setMake] = useState(params.make);
  const [model, setModel] = useState(params.model);
  const [zip, setZip] = useState(params.zip_code);
  const [radius, setRadius] = useState(params.radius_miles);
  const [yearMin, setYearMin] = useState<string>(params.year_min?.toString() ?? "");
  const [yearMax, setYearMax] = useState<string>(params.year_max?.toString() ?? "");
  const [priceMin, setPriceMin] = useState<string>(params.price_min?.toString() ?? "");
  const [priceMax, setPriceMax] = useState<string>(params.price_max?.toString() ?? "");
  const [mileageMax, setMileageMax] = useState<string>(params.mileage_max?.toString() ?? "");
  const [condition, setCondition] = useState(params.condition);

  const handleSearch = () => {
    onSearch({
      make,
      model,
      zip_code: zip,
      radius_miles: radius,
      year_min: yearMin ? parseInt(yearMin) : undefined,
      year_max: yearMax ? parseInt(yearMax) : undefined,
      price_min: priceMin ? parseInt(priceMin) : undefined,
      price_max: priceMax ? parseInt(priceMax) : undefined,
      mileage_max: mileageMax ? parseInt(mileageMax) : undefined,
      condition,
    });
  };

  const handleQuickSearch = (m: string, mo: string) => {
    setMake(m);
    setModel(mo);
    onSearch({ make: m, model: mo });
  };

  return (
    <div className="space-y-4">
      {/* Main search row */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
        <div className="flex-1 grid grid-cols-[1fr_1fr_auto] gap-2">
          <input
            type="text"
            value={make}
            onChange={(e) => setMake(e.target.value)}
            placeholder="Make (e.g. Rivian)"
            className="min-w-0 bg-gray-800/80 border border-gray-700 rounded-lg px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
          />
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            placeholder="Model (e.g. R1S)"
            className="min-w-0 bg-gray-800/80 border border-gray-700 rounded-lg px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
          />
          <input
            type="text"
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            placeholder="ZIP"
            className="w-20 sm:w-28 bg-gray-800/80 border border-gray-700 rounded-lg px-3 sm:px-4 py-2.5 sm:py-3 text-sm sm:text-base text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
          />
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-3 sm:px-4 py-2.5 sm:py-3 rounded-lg border transition-colors ${
              showFilters
                ? "bg-blue-500/20 border-blue-500 text-blue-400"
                : "bg-gray-800/80 border-gray-700 text-gray-400 hover:text-white"
            }`}
          >
            {showFilters ? <X className="w-5 h-5" /> : <SlidersHorizontal className="w-5 h-5" />}
          </button>

          <button
            onClick={handleSearch}
            disabled={loading}
            className="flex-1 sm:flex-none px-5 sm:px-6 py-2.5 sm:py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-600/50 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
          >
            <Search className="w-4 h-4" />
            {loading ? "Searching…" : "Search"}
          </button>
        </div>
      </div>

      {/* Quick searches */}
      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
        <span className="text-xs text-gray-500 py-1 shrink-0">Popular:</span>
        {POPULAR_SEARCHES.map((s) => (
          <button
            key={s.label}
            onClick={() => handleQuickSearch(s.make, s.model)}
            className={`shrink-0 px-3 py-1 rounded-full text-xs font-medium transition-colors ${
              make === s.make && model === s.model
                ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                : "bg-gray-800 text-gray-400 hover:text-white border border-gray-700 hover:border-gray-600"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Expanded filters */}
      {showFilters && (
        <div className="bg-gray-800/60 border border-gray-700/50 rounded-xl p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Year Min</label>
            <input type="number" value={yearMin} onChange={(e) => setYearMin(e.target.value)} placeholder="2020" className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Year Max</label>
            <input type="number" value={yearMax} onChange={(e) => setYearMax(e.target.value)} placeholder="2025" className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Price Min</label>
            <input type="number" value={priceMin} onChange={(e) => setPriceMin(e.target.value)} placeholder="$30,000" className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Price Max</label>
            <input type="number" value={priceMax} onChange={(e) => setPriceMax(e.target.value)} placeholder="$100,000" className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Max Mileage</label>
            <input type="number" value={mileageMax} onChange={(e) => setMileageMax(e.target.value)} placeholder="50,000" className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Radius (miles)</label>
            <select value={radius} onChange={(e) => setRadius(parseInt(e.target.value))} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
              <option value="50">50 mi</option>
              <option value="100">100 mi</option>
              <option value="250">250 mi</option>
              <option value="500">500 mi</option>
              <option value="1000">Nationwide</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Condition</label>
            <select value={condition} onChange={(e) => setCondition(e.target.value)} className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white">
              <option value="all">All</option>
              <option value="new">New</option>
              <option value="used">Used</option>
              <option value="cpo">Certified Pre-Owned</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSearch}
              disabled={loading}
              className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold rounded-lg transition-colors"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
