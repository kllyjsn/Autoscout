import { ExternalLink, MapPin, Gauge, Calendar } from "lucide-react";
import type { Listing } from "../types/listing";
import { DealBadge } from "./DealBadge";
import { SourceBadge } from "./SourceBadge";

function fmt(n: number) {
  return n.toLocaleString("en-US");
}

function fmtPrice(n: number) {
  return "$" + n.toLocaleString("en-US");
}

export function ListingCard({ listing }: { listing: Listing }) {
  const pctClass =
    listing.price_vs_market < -5
      ? "text-emerald-400"
      : listing.price_vs_market > 5
        ? "text-red-400"
        : "text-gray-400";

  return (
    <div className="group relative bg-gray-800/60 backdrop-blur border border-gray-700/50 rounded-xl overflow-hidden hover:border-gray-600 transition-all duration-200 hover:shadow-lg hover:shadow-black/20">
      {/* Image */}
      <div className="relative aspect-[16/10] bg-gray-900 overflow-hidden">
        {listing.image_url ? (
          <img
            src={listing.image_url}
            alt={listing.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-600">
            <svg className="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
            </svg>
          </div>
        )}
        <div className="absolute top-2 left-2">
          <SourceBadge source={listing.source} />
        </div>
        <div className="absolute top-2 right-2">
          <DealBadge rating={listing.deal_rating} score={listing.deal_score} />
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="text-white font-semibold text-sm leading-tight mb-2 line-clamp-2">
          {listing.title}
        </h3>

        <div className="flex items-baseline gap-2 mb-3">
          <span className="text-2xl font-bold text-white">{fmtPrice(listing.price)}</span>
          <span className={`text-xs font-medium ${pctClass}`}>
            {listing.price_vs_market > 0 ? "+" : ""}
            {listing.price_vs_market.toFixed(1)}% vs market
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 mb-3">
          <div className="flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5" />
            <span>{fmt(listing.mileage)} mi</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" />
            <span>{listing.year}</span>
          </div>
          {(listing.location || listing.distance_miles != null) && (
            <div className="flex items-center gap-1.5 col-span-2">
              <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
              <span className="truncate">
                {listing.location}
                {listing.distance_miles != null && (
                  <span className="text-blue-400 ml-1">
                    ({fmt(listing.distance_miles)} mi away)
                  </span>
                )}
              </span>
            </div>
          )}
        </div>

        {listing.dealer_name && (
          <p className="text-xs text-gray-500 truncate mb-3">{listing.dealer_name}</p>
        )}

        {listing.listing_url && (
          <a
            href={listing.listing_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors py-1.5"
          >
            View on {listing.source}
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );
}
