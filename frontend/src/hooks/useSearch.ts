import { useState, useCallback } from "react";
import { searchListings } from "../api/client";
import type { SearchParams, SearchResponse } from "../types/listing";

const DEFAULT_PARAMS: SearchParams = {
  make: "Rivian",
  model: "R1S",
  zip_code: "10001",
  radius_miles: 500,
  condition: "all",
};

export function useSearch() {
  const [params, setParams] = useState<SearchParams>(DEFAULT_PARAMS);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (overrides?: Partial<SearchParams>) => {
    const merged = { ...params, ...overrides };
    if (overrides) setParams(merged);
    setLoading(true);
    setError(null);
    try {
      const result = await searchListings(merged);
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }, [params]);

  return { params, setParams, data, loading, error, search };
}
