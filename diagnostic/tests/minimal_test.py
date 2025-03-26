from bs4 import BeautifulSoup
import requests
import logging
import json

# Configure basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("MinimalTest")

# Simple request with minimal headers
url = "https://www.indeed.com/jobs?q=python+developer"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

try:
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.select("div.job_seen_beacon")
        logger.info(f"Found {len(job_cards)} job cards")
        
        # Save first job for inspection
        if job_cards:
            first_job = job_cards[0]
            title_elem = first_job.select_one("h2.jobTitle span")
            title = title_elem.text.strip() if title_elem else "Unknown"
            logger.info(f"First job: {title}")
    else:
        logger.error(f"Request failed with status code: {response.status_code}")
except Exception as e:
    logger.error(f"Error during request: {e}")