# AutoScout — Car Market Aggregator

Every listing. Every source. Best deal.

AutoScout aggregates car listings from multiple major marketplaces (AutoTrader, CarMax, CarGurus, Cars.com, Carvana) into a single view with deal scoring, price analytics, and smart filters.

## Features

- **Multi-source aggregation** — scrapes listings from 5+ car marketplaces simultaneously
- **Deal scoring algorithm** — rates each listing as Great/Good/Fair/Overpriced based on price percentile, mileage-adjusted value, source reliability, and condition
- **Market analytics dashboard** — price distribution, price vs. mileage scatter plots, average price by year and source
- **Smart filters** — year, price range, mileage, condition, search radius, source
- **Real-time data** — Playwright-based browser scraping with JSON cache fallback

## Architecture

```
Frontend (React + TypeScript + Vite + Tailwind CSS)
  → REST API →
Backend (FastAPI + Python)
  → Scraper Engine (httpx + BeautifulSoup + Playwright)
    → CarGurus, Cars.com, AutoTrader, Carvana, CarMax
  → Deal Scoring Engine
  → Market Analytics
```

## Tech Stack

### Frontend
- React 19 + TypeScript
- Vite
- Tailwind CSS v4
- Recharts (analytics charts)
- Lucide React (icons)

### Backend
- Python 3.12 + FastAPI
- httpx + BeautifulSoup4 (HTTP scraping)
- Playwright (browser-based scraping)
- Pydantic v2 (data models)

## Development

### Backend
```bash
cd api
pip install fastapi uvicorn httpx beautifulsoup4 pydantic lxml
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Scraping real data
```bash
pip install playwright
python scrape_listings.py
```

## Default Test: Rivian R1S

The app comes pre-loaded with a Rivian R1S search — real listings scraped from AutoTrader and CarMax with prices, mileage, dealer info, and direct links to original listings.
