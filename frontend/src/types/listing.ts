export type Source =
  | "CarGurus"
  | "Cars.com"
  | "AutoTrader"
  | "Carvana"
  | "CarMax"
  | "Facebook Marketplace"
  | "Craigslist"
  | "TrueCar"
  | "Edmunds";

export type DealRating = "Great Deal" | "Good Deal" | "Fair Deal" | "Overpriced" | "Unknown";

export interface Listing {
  id: string;
  source: Source;
  title: string;
  year: number;
  make: string;
  model: string;
  trim: string;
  price: number;
  mileage: number;
  exterior_color: string;
  interior_color: string;
  drivetrain: string;
  fuel_type: string;
  transmission: string;
  engine: string;
  vin: string;
  dealer_name: string;
  dealer_rating: number | null;
  location: string;
  distance_miles: number | null;
  days_on_market: number | null;
  image_url: string;
  listing_url: string;
  condition: string;
  deal_rating: DealRating;
  deal_score: number;
  price_vs_market: number;
}

export interface SearchParams {
  make: string;
  model: string;
  zip_code: string;
  radius_miles: number;
  year_min?: number;
  year_max?: number;
  price_min?: number;
  price_max?: number;
  mileage_max?: number;
  condition: string;
}

export interface MarketAnalytics {
  total_listings: number;
  median_price: number;
  mean_price: number;
  min_price: number;
  max_price: number;
  avg_mileage: number;
  median_mileage: number;
  price_std_dev: number;
  listings_by_source: Record<string, number>;
  avg_price_by_source: Record<string, number>;
  avg_price_by_year: Record<string, number>;
  price_histogram: { bin_start: number; bin_end: number; count: number }[];
  price_vs_mileage: {
    price: number;
    mileage: number;
    year: number;
    source: string;
    title: string;
    deal_rating: string;
  }[];
  great_deals_count: number;
  good_deals_count: number;
  fair_deals_count: number;
  overpriced_count: number;
}

export interface SearchResponse {
  listings: Listing[];
  analytics: MarketAnalytics;
  query: SearchParams;
  sources_queried: string[];
  sources_succeeded: string[];
  sources_failed: string[];
}

export type SortField = "deal_score" | "price_asc" | "price_desc" | "mileage" | "year";
