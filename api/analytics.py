from __future__ import annotations

import math
import statistics
from collections import defaultdict

from models import DealRating, Listing, MarketAnalytics


def compute_analytics(listings: list[Listing]) -> MarketAnalytics:
    if not listings:
        return _empty_analytics()

    prices = [l.price for l in listings]
    mileages = [l.mileage for l in listings if l.mileage > 0]

    # Listings by source
    by_source: dict[str, list[Listing]] = defaultdict(list)
    for l in listings:
        by_source[l.source.value].append(l)

    listings_by_source = {k: len(v) for k, v in by_source.items()}
    avg_price_by_source = {
        k: int(statistics.mean(l.price for l in v))
        for k, v in by_source.items()
    }

    # Avg price by year
    by_year: dict[int, list[int]] = defaultdict(list)
    for l in listings:
        by_year[l.year].append(l.price)
    avg_price_by_year = {
        y: int(statistics.mean(ps)) for y, ps in sorted(by_year.items())
    }

    # Price histogram (10 bins)
    price_histogram = _histogram(prices, bins=10)

    # Price vs mileage scatter data
    price_vs_mileage = [
        {"price": l.price, "mileage": l.mileage, "year": l.year,
         "source": l.source.value, "title": l.title, "deal_rating": l.deal_rating.value}
        for l in listings if l.mileage > 0
    ]

    # Deal rating counts
    deal_counts = defaultdict(int)
    for l in listings:
        deal_counts[l.deal_rating] += 1

    return MarketAnalytics(
        total_listings=len(listings),
        median_price=int(statistics.median(prices)),
        mean_price=int(statistics.mean(prices)),
        min_price=min(prices),
        max_price=max(prices),
        avg_mileage=int(statistics.mean(mileages)) if mileages else 0,
        median_mileage=int(statistics.median(mileages)) if mileages else 0,
        price_std_dev=round(statistics.stdev(prices), 2) if len(prices) > 1 else 0.0,
        listings_by_source=listings_by_source,
        avg_price_by_source=avg_price_by_source,
        avg_price_by_year=avg_price_by_year,
        price_histogram=price_histogram,
        price_vs_mileage=price_vs_mileage,
        great_deals_count=deal_counts.get(DealRating.GREAT, 0),
        good_deals_count=deal_counts.get(DealRating.GOOD, 0),
        fair_deals_count=deal_counts.get(DealRating.FAIR, 0),
        overpriced_count=deal_counts.get(DealRating.OVERPRICED, 0),
    )


def _histogram(values: list[int], bins: int = 10) -> list[dict]:
    if not values:
        return []
    min_val = min(values)
    max_val = max(values)
    if min_val == max_val:
        return [{"bin_start": min_val, "bin_end": max_val, "count": len(values)}]

    bin_width = math.ceil((max_val - min_val) / bins)
    result = []
    for i in range(bins):
        start = min_val + i * bin_width
        end = start + bin_width
        count = sum(1 for v in values if start <= v < end or (i == bins - 1 and v == max_val))
        result.append({"bin_start": start, "bin_end": end, "count": count})
    return result


def _empty_analytics() -> MarketAnalytics:
    return MarketAnalytics(
        total_listings=0, median_price=0, mean_price=0, min_price=0, max_price=0,
        avg_mileage=0, median_mileage=0, price_std_dev=0.0,
        listings_by_source={}, avg_price_by_source={}, avg_price_by_year={},
        price_histogram=[], price_vs_mileage=[],
        great_deals_count=0, good_deals_count=0, fair_deals_count=0, overpriced_count=0,
    )
