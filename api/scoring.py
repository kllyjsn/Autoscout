from __future__ import annotations

import statistics
from models import DealRating, Listing


def score_listings(listings: list[Listing]) -> list[Listing]:
    """Score all listings relative to the market and assign deal ratings."""
    if not listings:
        return listings

    prices = [l.price for l in listings]
    mileages = [l.mileage for l in listings if l.mileage > 0]

    if not prices:
        return listings

    median_price = statistics.median(prices)
    mean_price = statistics.mean(prices)
    price_stdev = statistics.stdev(prices) if len(prices) > 1 else 1.0
    median_mileage = statistics.median(mileages) if mileages else 0
    mean_mileage = statistics.mean(mileages) if mileages else 0

    for listing in listings:
        score = _compute_score(
            listing, median_price, mean_price, price_stdev,
            median_mileage, mean_mileage,
        )
        listing.deal_score = round(score, 1)
        listing.deal_rating = _rating_from_score(score)
        listing.price_vs_market = round(
            ((listing.price - median_price) / median_price) * 100, 1
        ) if median_price > 0 else 0.0

    return listings


def _compute_score(
    listing: Listing,
    median_price: float,
    mean_price: float,
    price_stdev: float,
    median_mileage: float,
    mean_mileage: float,
) -> float:
    # Price score (40%): how far below market price
    price_z = (mean_price - listing.price) / price_stdev if price_stdev > 0 else 0
    price_score = min(max((price_z + 2) / 4 * 100, 0), 100)

    # Mileage-adjusted value (25%): lower mileage at same price = better
    if listing.mileage > 0 and median_mileage > 0:
        mileage_ratio = median_mileage / listing.mileage
        mileage_score = min(max(mileage_ratio * 50, 0), 100)
    else:
        mileage_score = 50.0

    # Source reliability (10%)
    source_scores = {
        "CarGurus": 80, "Cars.com": 75, "AutoTrader": 75,
        "Carvana": 85, "CarMax": 85, "TrueCar": 80,
        "Facebook Marketplace": 50, "Craigslist": 40,
        "Edmunds": 75,
    }
    source_score = source_scores.get(listing.source.value, 60)

    # Days on market (10%): longer = more negotiable = better deal potential
    if listing.days_on_market is not None:
        dom_score = min(listing.days_on_market / 60 * 100, 100)
    else:
        dom_score = 50.0

    # Condition factor (15%)
    condition_scores = {
        "New": 90, "Certified Pre-Owned": 85, "CPO": 85,
        "Used": 60, "Like New": 80,
    }
    condition_score = condition_scores.get(listing.condition, 60)

    return (
        price_score * 0.40
        + mileage_score * 0.25
        + source_score * 0.10
        + dom_score * 0.10
        + condition_score * 0.15
    )


def _rating_from_score(score: float) -> DealRating:
    if score >= 75:
        return DealRating.GREAT
    if score >= 60:
        return DealRating.GOOD
    if score >= 45:
        return DealRating.FAIR
    return DealRating.OVERPRICED
