"""Scrape car listings from major sites for multiple makes/models using Playwright + CDP."""
import asyncio
import json
import re
import hashlib
import sys

from playwright.async_api import async_playwright, Page


def make_id(*parts: str) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.md5(raw.encode()).hexdigest()[:12]


MODELS_TO_SCRAPE = [
    {"make": "Rivian", "model": "R1S", "fuel": "Electric"},
    {"make": "Rivian", "model": "R1T", "fuel": "Electric"},
    {"make": "Tesla", "model": "Model Y", "fuel": "Electric"},
    {"make": "Tesla", "model": "Model 3", "fuel": "Electric"},
    {"make": "Ford", "model": "F-150 Lightning", "fuel": "Electric"},
    {"make": "BMW", "model": "iX", "fuel": "Electric"},
    {"make": "Porsche", "model": "Taycan", "fuel": "Electric"},
]


def build_autotrader_url(make: str, model: str) -> str:
    m = make.lower()
    mo = model.lower().replace(" ", "-").replace("-", "-")
    return f"https://www.autotrader.com/cars-for-sale/all-cars/{m}/{mo}?zip=10001&searchRadius=500&numRecords=50"


def build_carmax_url(make: str, model: str) -> str:
    m = make.lower()
    mo = model.lower().replace(" ", "-")
    return f"https://www.carmax.com/cars/{m}/{mo}"


def build_cargurus_slug(make: str, model: str) -> str:
    """Build CarGurus search URL."""
    m = make.lower()
    mo = model.lower().replace(" ", "+")
    return f"https://www.cargurus.com/Cars/l-Used-{make}-{model.replace(' ', '-')}-t{m[0:3]}"


def build_carscom_url(make: str, model: str) -> str:
    m = make.lower()
    mo = f"{m}-{model.lower().replace(' ', '-')}"
    return f"https://www.cars.com/shopping/results/?stock_type=all&makes[]={m}&models[]={mo}&zip=10001&maximum_distance=500&page_size=50"


def build_carvana_url(make: str, model: str) -> str:
    m = make.lower()
    mo = model.lower().replace(" ", "-")
    return f"https://www.carvana.com/cars/{m}-{mo}"


async def scrape_autotrader(page: Page, make: str, model: str, fuel: str) -> list[dict]:
    listings = []
    try:
        url = build_autotrader_url(make, model)
        print(f"  AutoTrader: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        data = await page.evaluate(r"""() => {
            const results = [];
            const cards = document.querySelectorAll('[data-cmp="inventoryListing"]');
            for (const card of cards) {
                try {
                    const title = card.querySelector('h2')?.textContent?.trim() || '';
                    const priceText = card.querySelector('[data-cmp="firstPrice"]')?.textContent?.trim() || '';
                    const specs = card.querySelectorAll('[data-cmp="listingCardFeature"] li, .text-bold-sm');
                    let mileageText = '';
                    for (const s of specs) {
                        const t = s.textContent.trim();
                        if (t.includes('mi') || t.includes('mile')) { mileageText = t; break; }
                    }
                    const dealer = card.querySelector('[data-cmp="dealerName"]')?.textContent?.trim() || '';
                    const img = card.querySelector('img')?.src || '';
                    const link = card.querySelector('a[href*="vehicledetails"]')?.href || '';
                    if (title && priceText) {
                        results.push({title, price: priceText, mileage: mileageText, dealer, image: img, url: link});
                    }
                } catch(e) {}
            }
            return results;
        }""")

        for item in data:
            price = int(re.sub(r"[^\d]", "", item.get("price", "0")) or 0)
            mileage_text = item.get("mileage", "0")
            mileage = int(re.sub(r"[^\d]", "", mileage_text) or 0)
            if price <= 0 or price > 300000:
                continue
            title = item.get("title", "")
            year_match = re.match(r"(\d{4})", title)
            year = int(year_match.group(1)) if year_match else 2024
            listings.append({
                "id": make_id("autotrader", title, str(price)),
                "source": "AutoTrader", "title": title, "year": year,
                "make": make, "model": model, "trim": "", "price": price,
                "mileage": mileage, "dealer_name": item.get("dealer", ""),
                "image_url": item.get("image", ""), "listing_url": item.get("url", ""),
                "condition": "Used", "fuel_type": fuel,
            })
        print(f"    -> {len(listings)} listings")
    except Exception as e:
        print(f"    AutoTrader error: {e}")
    return listings


async def scrape_carmax(page: Page, make: str, model: str, fuel: str) -> list[dict]:
    listings = []
    try:
        url = build_carmax_url(make, model)
        print(f"  CarMax: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        data = await page.evaluate(r"""() => {
            const results = [];
            const tiles = document.querySelectorAll('[data-id].kmx-car-tile, .MuiCard-root.kmx-car-tile');
            for (const tile of tiles) {
                try {
                    const clickProps = tile.getAttribute('data-clickprops') || '';
                    const priceMatch = clickProps.match(/Price:\s*(\d+)/);
                    const ymmMatch = clickProps.match(/YMM:\s*([\w\s]+?)(?:,|$)/);
                    const stockMatch = clickProps.match(/StockNumber:\s*(\d+)/);
                    const titleEl = tile.querySelector('h3, [class*="car-title"], .kmx-car-tile__title');
                    const title = titleEl ? titleEl.textContent.trim() : (ymmMatch ? ymmMatch[1] : '');
                    let price = priceMatch ? priceMatch[1] : '';
                    if (!price) {
                        const priceEl = tile.querySelector('[class*="price"]');
                        price = priceEl ? priceEl.textContent.replace(/[^0-9]/g, '') : '';
                    }
                    const bodyText = tile.textContent;
                    const mileageMatch = bodyText.match(/(\d+)K\s*mi/i);
                    const mileage = mileageMatch ? String(parseInt(mileageMatch[1]) * 1000) : '0';
                    const locMatch = bodyText.match(/CarMax\s+(.+?)(?:\n|Est)/);
                    const location = locMatch ? locMatch[1].trim() : '';
                    const img = tile.querySelector('img')?.src || '';
                    const stockNo = tile.getAttribute('data-id') || (stockMatch ? stockMatch[1] : '');
                    const link = stockNo ? '/car/' + stockNo : '';
                    if (title && price) {
                        results.push({title, price, mileage, image: img, url: link, location, stockNo: stockNo});
                    }
                } catch(e) {}
            }
            return results;
        }""")

        seen_urls = set()
        for item in data:
            price = int(item.get("price", "0") or 0)
            mileage = int(item.get("mileage", "0") or 0)
            if price <= 0 or price > 300000:
                continue
            stock_no = item.get("stockNo", "")
            listing_url = f"https://www.carmax.com/car/{stock_no}" if stock_no else ""
            if listing_url in seen_urls:
                continue
            seen_urls.add(listing_url)
            title = item.get("title", "")
            year_match = re.match(r"(\d{4})", title)
            year = int(year_match.group(1)) if year_match else 2024
            listings.append({
                "id": make_id("carmax", stock_no, str(price)),
                "source": "CarMax", "title": title, "year": year,
                "make": make, "model": model, "trim": "", "price": price,
                "mileage": mileage, "dealer_name": "CarMax",
                "location": item.get("location", ""),
                "image_url": item.get("image", ""), "listing_url": listing_url,
                "condition": "Used", "fuel_type": fuel,
            })
        print(f"    -> {len(listings)} listings")
    except Exception as e:
        print(f"    CarMax error: {e}")
    return listings


async def scrape_carscom(page: Page, make: str, model: str, fuel: str) -> list[dict]:
    listings = []
    try:
        url = build_carscom_url(make, model)
        print(f"  Cars.com: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        data = await page.evaluate(r"""() => {
            const results = [];
            const cards = document.querySelectorAll('.vehicle-card');
            for (const card of cards) {
                try {
                    const title = card.querySelector('h2')?.textContent?.trim() || '';
                    const priceText = card.querySelector('.primary-price')?.textContent?.trim() || '';
                    const mileageText = card.querySelector('.mileage')?.textContent?.trim() || '';
                    const dealer = card.querySelector('.dealer-name')?.textContent?.trim() || '';
                    const img = card.querySelector('img')?.src || '';
                    const link = card.querySelector('a')?.href || '';
                    const location = card.querySelector('.miles-from')?.textContent?.trim() || '';
                    if (title && priceText.includes('$')) {
                        results.push({title, price: priceText, mileage: mileageText, dealer, image: img, url: link, location});
                    }
                } catch(e) {}
            }
            return results;
        }""")

        for item in data:
            price_text = item.get("price", "0")
            price = int(re.sub(r"[^\d]", "", price_text.split("$")[-1].split(" ")[0]) or 0)
            mileage_text = item.get("mileage", "0")
            mileage = int(re.sub(r"[^\d]", "", mileage_text) or 0)
            if price <= 0 or price > 300000:
                continue
            title = item.get("title", "")
            year_match = re.match(r"(\d{4})", title)
            year = int(year_match.group(1)) if year_match else 2024
            listing_url = item.get("url", "")
            if listing_url and not listing_url.startswith("http"):
                listing_url = f"https://www.cars.com{listing_url}"
            listings.append({
                "id": make_id("carscom", title, str(price)),
                "source": "Cars.com", "title": title, "year": year,
                "make": make, "model": model, "trim": "", "price": price,
                "mileage": mileage, "dealer_name": item.get("dealer", ""),
                "location": item.get("location", ""),
                "image_url": item.get("image", ""), "listing_url": listing_url,
                "condition": "Used", "fuel_type": fuel,
            })
        print(f"    -> {len(listings)} listings")
    except Exception as e:
        print(f"    Cars.com error: {e}")
    return listings


async def scrape_carvana(page: Page, make: str, model: str, fuel: str) -> list[dict]:
    listings = []
    try:
        url = build_carvana_url(make, model)
        print(f"  Carvana: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)

        data = await page.evaluate(r"""() => {
            const results = [];
            const cards = document.querySelectorAll('[data-test="ResultTile"], article, [class*="result-tile"]');
            for (const card of cards) {
                try {
                    const title = (card.querySelector('[data-test="TileTitle"], h2, [class*="year-make"]') || {}).textContent?.trim() || '';
                    const priceText = (card.querySelector('[data-test="TilePrice"], [class*="price"]') || {}).textContent?.trim() || '';
                    const mileageText = (card.querySelector('[data-test="TileMileage"], [class*="mileage"]') || {}).textContent?.trim() || '';
                    const img = card.querySelector('img')?.src || '';
                    const link = card.querySelector('a[href*="/vehicle/"]')?.href || '';
                    if (title && priceText.includes('$')) {
                        results.push({title, price: priceText, mileage: mileageText, image: img, url: link});
                    }
                } catch(e) {}
            }
            return results;
        }""")

        for item in data:
            price = int(re.sub(r"[^\d]", "", item.get("price", "0").split("$")[-1].split(" ")[0]) or 0)
            mileage = int(re.sub(r"[^\d]", "", item.get("mileage", "0")) or 0)
            if price <= 0 or price > 300000:
                continue
            title = item.get("title", "")
            year_match = re.match(r"(\d{4})", title)
            year = int(year_match.group(1)) if year_match else 2024
            listing_url = item.get("url", "")
            if listing_url and not listing_url.startswith("http"):
                listing_url = f"https://www.carvana.com{listing_url}"
            listings.append({
                "id": make_id("carvana", title, str(price)),
                "source": "Carvana", "title": title, "year": year,
                "make": make, "model": model, "trim": "", "price": price,
                "mileage": mileage, "dealer_name": "Carvana",
                "image_url": item.get("image", ""), "listing_url": listing_url,
                "condition": "Used", "fuel_type": fuel,
            })
        print(f"    -> {len(listings)} listings")
    except Exception as e:
        print(f"    Carvana error: {e}")
    return listings


async def main():
    all_listings = []

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://localhost:29229")
        context = browser.contexts[0] if browser.contexts else await browser.new_context()

        for car in MODELS_TO_SCRAPE:
            make = car["make"]
            model = car["model"]
            fuel = car["fuel"]
            print(f"\n{'='*60}")
            print(f"Scraping {make} {model}...")
            print(f"{'='*60}")

            scrapers = [
                ("AutoTrader", scrape_autotrader),
                ("CarMax", scrape_carmax),
                ("Cars.com", scrape_carscom),
                ("Carvana", scrape_carvana),
            ]

            for name, scraper_fn in scrapers:
                page = await context.new_page()
                try:
                    results = await scraper_fn(page, make, model, fuel)
                    all_listings.extend(results)
                finally:
                    await page.close()

    # Deduplicate by (source, title, price)
    seen = set()
    deduped = []
    for l in all_listings:
        key = (l["source"], l["title"], l["price"])
        if key not in seen:
            seen.add(key)
            deduped.append(l)
    all_listings = deduped

    # Summary
    print(f"\n{'='*60}")
    print(f"TOTAL: {len(all_listings)} listings scraped")
    by_model = {}
    for l in all_listings:
        k = f"{l['make']} {l['model']}"
        by_model[k] = by_model.get(k, 0) + 1
    for k, v in sorted(by_model.items()):
        print(f"  {k}: {v}")
    print(f"{'='*60}")

    output_path = "/home/ubuntu/autoscout/api/scraped_data.json"
    with open(output_path, "w") as f:
        json.dump(all_listings, f, indent=2)
    print(f"Saved to {output_path}")
    return all_listings


if __name__ == "__main__":
    listings = asyncio.run(main())
    sys.exit(0 if listings else 1)
