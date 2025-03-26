# scrapers/__init__.py - Initialize scrapers package
from .indeed_scraper import IndeedScraper
from .remoteok_scraper import RemoteOKScraper

# Add more scrapers as they are implemented
available_scrapers = {
    "Indeed": IndeedScraper,
    "RemoteOK": RemoteOKScraper
}

def get_scraper(name):
    """Get a scraper instance by name"""
    if name in available_scrapers:
        return available_scrapers[name]()
    return None

def get_all_scrapers():
    """Get instances of all available scrapers"""
    return {name: scraper_class() for name, scraper_class in available_scrapers.items()}