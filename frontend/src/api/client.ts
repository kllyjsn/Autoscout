import type { SearchParams, SearchResponse } from "../types/listing";

const API_BASE = import.meta.env.VITE_API_URL || "";

export async function searchListings(
  params: Partial<SearchParams>
): Promise<SearchResponse> {
  const query = new URLSearchParams();

  if (params.make) query.set("make", params.make);
  if (params.model) query.set("model", params.model);
  if (params.zip_code) query.set("zip_code", params.zip_code);
  if (params.radius_miles) query.set("radius_miles", String(params.radius_miles));
  if (params.year_min) query.set("year_min", String(params.year_min));
  if (params.year_max) query.set("year_max", String(params.year_max));
  if (params.price_min) query.set("price_min", String(params.price_min));
  if (params.price_max) query.set("price_max", String(params.price_max));
  if (params.mileage_max) query.set("mileage_max", String(params.mileage_max));
  if (params.condition) query.set("condition", params.condition);

  const resp = await fetch(`${API_BASE}/api/search?${query.toString()}`);
  if (!resp.ok) {
    throw new Error(`Search failed: ${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}
