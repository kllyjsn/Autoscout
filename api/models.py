from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Source(str, Enum):
    CARGURUS = "CarGurus"
    CARS_COM = "Cars.com"
    AUTOTRADER = "AutoTrader"
    CARVANA = "Carvana"
    CARMAX = "CarMax"
    FACEBOOK = "Facebook Marketplace"
    CRAIGSLIST = "Craigslist"
    TRUECAR = "TrueCar"
    EDMUNDS = "Edmunds"


class DealRating(str, Enum):
    GREAT = "Great Deal"
    GOOD = "Good Deal"
    FAIR = "Fair Deal"
    OVERPRICED = "Overpriced"
    UNKNOWN = "Unknown"


class Listing(BaseModel):
    id: str
    source: Source
    title: str
    year: int
    make: str
    model: str
    trim: str = ""
    price: int
    mileage: int
    exterior_color: str = ""
    interior_color: str = ""
    drivetrain: str = ""
    fuel_type: str = "Electric"
    transmission: str = ""
    engine: str = ""
    vin: str = ""
    dealer_name: str = ""
    dealer_rating: float | None = None
    location: str = ""
    distance_miles: int | None = None
    days_on_market: int | None = None
    image_url: str = ""
    listing_url: str = ""
    condition: str = "Used"
    deal_rating: DealRating = DealRating.UNKNOWN
    deal_score: float = 0.0
    price_vs_market: float = 0.0  # % above/below market avg


class SearchParams(BaseModel):
    make: str = "Rivian"
    model: str = "R1S"
    zip_code: str = "10001"
    radius_miles: int = 500
    year_min: int | None = None
    year_max: int | None = None
    price_min: int | None = None
    price_max: int | None = None
    mileage_max: int | None = None
    condition: str = "all"  # "new", "used", "cpo", "all"


class MarketAnalytics(BaseModel):
    total_listings: int
    median_price: int
    mean_price: int
    min_price: int
    max_price: int
    avg_mileage: int
    median_mileage: int
    price_std_dev: float
    listings_by_source: dict[str, int]
    avg_price_by_source: dict[str, int]
    avg_price_by_year: dict[int, int]
    price_histogram: list[dict]
    price_vs_mileage: list[dict]
    great_deals_count: int
    good_deals_count: int
    fair_deals_count: int
    overpriced_count: int


class SearchResponse(BaseModel):
    listings: list[Listing]
    analytics: MarketAnalytics
    query: SearchParams
    sources_queried: list[str]
    sources_succeeded: list[str]
    sources_failed: list[str]
