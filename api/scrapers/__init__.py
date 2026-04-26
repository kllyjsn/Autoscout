from scrapers.cargurus import CarGurusScraper
from scrapers.cars_com import CarsComScraper
from scrapers.autotrader import AutoTraderScraper
from scrapers.carvana import CarvanaScraper
from scrapers.carmax import CarMaxScraper

ALL_SCRAPERS = [
    CarGurusScraper,
    CarsComScraper,
    AutoTraderScraper,
    CarvanaScraper,
    CarMaxScraper,
]

__all__ = [
    "ALL_SCRAPERS",
    "CarGurusScraper",
    "CarsComScraper",
    "AutoTraderScraper",
    "CarvanaScraper",
    "CarMaxScraper",
]
