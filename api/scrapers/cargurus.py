from __future__ import annotations

import json
import logging

from models import Listing, SearchParams, Source
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

# CarGurus entity IDs — verified by probing the JSON API.
# Format: "make_model" (lowercased) -> entity ID.
ENTITY_MAP: dict[str, str] = {
    # Toyota
    "toyota_camry": "d292",
    "toyota_corolla": "d295",
    "toyota_rav4": "d306",
    "toyota_highlander": "d298",
    "toyota_tacoma": "d311",
    "toyota_4runner": "d290",
    "toyota_tundra": "d313",
    "toyota_prius": "d15",
    "toyota_supra": "d309",
    "toyota_sienna": "d308",
    "toyota_sequoia": "d307",
    "toyota_avalon": "d291",
    "toyota_fj cruiser": "d826",
    "toyota_yaris": "d827",
    # Honda
    "honda_civic": "d586",
    "honda_accord": "d585",
    "honda_cr-v": "d589",
    "honda_pilot": "d594",
    "honda_odyssey": "d592",
    "honda_fit": "d744",
    "honda_ridgeline": "d734",
    "honda_s2000": "d596",
    "honda_element": "d590",
    # Ford
    "ford_f-150": "d337",
    "ford_mustang": "d352",
    "ford_explorer": "d334",
    "ford_escape": "d330",
    "ford_bronco": "d320",
    "ford_edge": "d923",
    "ford_expedition": "d333",
    "ford_ranger": "d354",
    "ford_focus": "d346",
    "ford_fusion": "d845",
    "ford_taurus": "d355",
    "ford_gt": "d350",
    # Chevrolet
    "chevrolet_silverado 1500": "d630",
    "chevrolet_equinox": "d616",
    "chevrolet_tahoe": "d639",
    "chevrolet_camaro": "d606",
    "chevrolet_corvette": "d1",
    "chevrolet_malibu": "d622",
    "chevrolet_colorado": "d614",
    "chevrolet_suburban": "d638",
    "chevrolet_impala": "d619",
    "chevrolet_trailblazer": "d642",
    "chevrolet_blazer": "d602",
    # BMW
    "bmw_3 series": "d390",
    "bmw_m3": "d390",
    "bmw_m5": "d391",
    "bmw_x3": "d392",
    "bmw_x5": "d393",
    "bmw_z4": "d395",
    "bmw_m6": "d825",
    # Mercedes-Benz
    "mercedes-benz_c-class": "d66",
    "mercedes-benz_e-class": "d76",
    "mercedes-benz_s-class": "d82",
    "mercedes-benz_g-class": "d78",
    "mercedes-benz_cls": "d751",
    "mercedes-benz_sl-class": "d84",
    "mercedes-benz_r-class": "d829",
    "mercedes-benz_gl-class": "d936",
    # Porsche
    "porsche_911": "d404",
    "porsche_boxster": "d408",
    "porsche_cayenne": "d410",
    "porsche_cayman": "d993",
    # Audi
    "audi_a3": "d24",
    "audi_a4": "d25",
    "audi_a6": "d27",
    "audi_a8": "d29",
    "audi_s4": "d30",
    "audi_tt": "d32",
    "audi_q7": "d930",
    "audi_rs 4": "d992",
    "audi_rs 6": "d686",
    # Hyundai
    "hyundai_tucson": "d98",
    "hyundai_santa fe": "d94",
    "hyundai_sonata": "d96",
    "hyundai_elantra": "d92",
    "hyundai_accent": "d91",
    # Kia
    "kia_optima": "d158",
    "kia_sorento": "d162",
    "kia_sportage": "d164",
    "kia_rio": "d159",
    "kia_sedona": "d160",
    # Subaru
    "subaru_outback": "d380",
    "subaru_forester": "d374",
    "subaru_impreza": "d375",
    "subaru_legacy": "d378",
    "subaru_wrx sti": "d376",
    # Jeep
    "jeep_wrangler": "d494",
    "jeep_grand cherokee": "d490",
    "jeep_cherokee": "d488",
    "jeep_liberty": "d492",
    "jeep_compass": "d905",
    "jeep_commander": "d849",
    # Dodge
    "dodge_challenger": "d894",
    "dodge_charger": "d733",
    "dodge_durango": "d651",
    "dodge_ram 1500": "d665",
    # GMC
    "gmc_sierra 1500": "d116",
    "gmc_yukon": "d130",
    "gmc_acadia": "d925",
    "gmc_canyon": "d103",
    # Lexus
    "lexus_gs hybrid": "d918",
    # Nissan
    "nissan_altima": "d237",
    "nissan_maxima": "d242",
    "nissan_murano": "d243",
    "nissan_pathfinder": "d245",
    "nissan_frontier": "d240",
    "nissan_sentra": "d249",
    "nissan_titan": "d251",
    "nissan_xterra": "d253",
    "nissan_350z": "d236",
    "nissan_armada": "d238",
    "nissan_versa": "d937",
    # Volkswagen
    "volkswagen_jetta": "d200",
    "volkswagen_passat": "d202",
    "volkswagen_golf": "d198",
    "volkswagen_gti": "d199",
    "volkswagen_touareg": "d205",
    "volkswagen_beetle": "d201",
    "volkswagen_tiguan": "d839",
    "volkswagen_rabbit": "d839",
    # INFINITI
    "infiniti_g35": "d576",
    "infiniti_fx35": "d573",
    "infiniti_q45": "d582",
    "infiniti_qx56": "d584",
    "infiniti_m35": "d735",
    # Acura
    "acura_mdx": "d16",
    "acura_tl": "d19",
    "acura_tsx": "d20",
    "acura_rdx": "d921",
    "acura_rsx": "d3",
    "acura_integra": "d36",
    # Lincoln
    "lincoln_navigator": "d530",
    "lincoln_town car": "d531",
    "lincoln_mkx": "d928",
    "lincoln_mkz": "d974",
    "lincoln_aviator": "d524",
    # Cadillac
    "cadillac_escalade": "d142",
    "cadillac_cts": "d138",
    "cadillac_cts-v": "d139",
    "cadillac_dts": "d732",
    "cadillac_srx": "d148",
    "cadillac_sts": "d149",
    # Volvo
    "volvo_xc90": "d523",
    "volvo_xc70": "d522",
    "volvo_s60": "d511",
    "volvo_s80": "d514",
    "volvo_c70": "d508",
    "volvo_v70": "d518",
    # Mazda
    "mazda_mazda3": "d214",
    "mazda_mazda6": "d215",
    "mazda_mx-5 miata": "d221",
    "mazda_cx-7": "d935",
    "mazda_rx-8": "d227",
    "mazda_tribute": "d228",
    # Land Rover
    "land rover_range rover": "d156",
    "land rover_range rover sport": "d834",
    "land rover_lr3": "d155",
    "land rover_lr2": "d927",
    "land rover_discovery": "d152",
    "land rover_defender": "d151",
    # Mitsubishi
    "mitsubishi_eclipse": "d417",
    "mitsubishi_outlander": "d429",
    "mitsubishi_lancer": "d422",
    "mitsubishi_lancer evolution": "d423",
    # Chrysler
    "chrysler_300": "d165",
    "chrysler_town & country": "d182",
    "chrysler_pacifica": "d177",
    "chrysler_sebring": "d180",
    "chrysler_pt cruiser": "d179",
    # Buick
    "buick_lacrosse": "d272",
    "buick_enclave": "d278",
    "buick_regal": "d277",
    "buick_lucerne": "d844",
    # Pontiac
    "pontiac_g6": "d467",
    "pontiac_grand prix": "d469",
    "pontiac_firebird": "d466",
    "pontiac_gto": "d470",
    "pontiac_solstice": "d737",
    "pontiac_g8": "d979",
    # Saturn
    "saturn_vue": "d538",
    "saturn_ion": "d532",
    "saturn_aura": "d938",
    "saturn_sky": "d939",
    # Hummer
    "hummer_h2": "d231",
    "hummer_h3": "d843",
    # Bentley
    "bentley_continental gt": "d35",
    "bentley_continental flying spur": "d34",
    # Lamborghini
    "lamborghini_gallardo": "d255",
    "lamborghini_murcielago": "d256",
    # Ferrari
    "ferrari_f430": "d443",
    "ferrari_360": "d437",
    "ferrari_599 gtb fiorano": "d959",
    # Aston Martin
    "aston martin_db9": "d908",
    "aston martin_v8 vantage": "d910",
    # Maserati
    "maserati_quattroporte": "d402",
    "maserati_gransport": "d401",
    # Rolls-Royce
    "rolls-royce_phantom": "d413",
    # Suzuki
    "suzuki_grand vitara": "d260",
    # MINI
    "mini_cooper": "d436",
}


class CarGurusScraper(BaseScraper):
    source = Source.CARGURUS
    base_url = "https://www.cargurus.com"

    async def search(self, params: SearchParams) -> list[Listing]:
        try:
            entity_key = f"{params.make.lower()}_{params.model.lower()}"
            entity_id = ENTITY_MAP.get(entity_key)

            if not entity_id:
                logger.info(f"CarGurus: no entity ID for {params.make} {params.model}, skipping")
                return []

            url = f"{self.base_url}/Cars/searchResults.action"
            query: dict[str, str] = {
                "zip": params.zip_code,
                "inventorySearchWidgetType": "AUTO",
                "sortDir": "ASC",
                "sortType": "DEAL",
                "distance": str(params.radius_miles),
                "entitySelectingHelper.selectedEntity": entity_id,
                "maxResults": "50",
            }
            if params.year_min:
                query["startYear"] = str(params.year_min)
            if params.year_max:
                query["endYear"] = str(params.year_max)
            if params.price_min:
                query["minPrice"] = str(params.price_min)
            if params.price_max:
                query["maxPrice"] = str(params.price_max)
            if params.mileage_max:
                query["maxMileage"] = str(params.mileage_max)

            resp = await self._get_json(url, params=query, headers={
                "X-Requested-With": "XMLHttpRequest",
            })

            raw = resp.text
            if raw == "null" or not raw.strip():
                return []

            data = json.loads(raw)
            if not isinstance(data, list):
                return []

            listings: list[Listing] = []
            for item in data:
                listing = self._parse_item(item, params)
                if listing:
                    listings.append(listing)

            logger.info(f"CarGurus: {len(listings)} listings")
            return listings

        except Exception:
            logger.exception("CarGurus scrape failed")
            return []

    def _parse_item(self, item: dict, params: SearchParams) -> Listing | None:
        try:
            price = int(item.get("price", 0) or 0)
            if price <= 0:
                return None

            year = int(item.get("carYear", 0))
            if year <= 0:
                return None

            make = item.get("makeName", params.make)
            model = item.get("modelName", params.model)
            trim = item.get("trimName", "")

            title = item.get("listingTitle", f"{year} {make} {model}")

            mileage = int(item.get("mileage", 0) or 0)

            listing_id = str(item.get("id", ""))
            vdp_url = item.get("vdpUrl", "")
            if vdp_url:
                listing_url = f"{self.base_url}{vdp_url}" if not vdp_url.startswith("http") else vdp_url
            elif listing_id:
                listing_url = f"{self.base_url}/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?#listing={listing_id}"
            else:
                listing_url = ""

            image_data = item.get("originalPictureData", {})
            image_url = ""
            if isinstance(image_data, dict):
                photos = image_data.get("photos", [])
                if photos and isinstance(photos, list):
                    first = photos[0]
                    image_url = first.get("url", "") if isinstance(first, dict) else str(first)

            days_on_market = item.get("daysOnMarket")

            seller_city = item.get("sellerCity", "")
            seller_region = item.get("sellerRegion", "")
            location = f"{seller_city}, {seller_region}" if seller_city else seller_region

            raw_distance = item.get("distance")
            distance_miles = round(raw_distance) if raw_distance is not None else None

            seller_rating = item.get("sellerRating")
            dealer_rating = float(seller_rating) if seller_rating is not None else None

            return Listing(
                id=self._make_id("cargurus", listing_id, str(price)),
                source=self.source,
                title=title,
                year=year,
                make=make,
                model=model,
                trim=trim,
                price=price,
                mileage=mileage,
                exterior_color=item.get("localizedExteriorColor", item.get("exteriorColorName", "")),
                vin=item.get("vin", ""),
                dealer_name=item.get("serviceProviderName", ""),
                dealer_rating=dealer_rating,
                location=location,
                distance_miles=distance_miles,
                days_on_market=int(days_on_market) if days_on_market is not None else None,
                image_url=image_url,
                listing_url=listing_url,
                transmission=item.get("localizedTransmission", ""),
                condition="Used",
            )
        except (ValueError, TypeError, KeyError):
            return None
