from bs4 import BeautifulSoup
import requests
import logging
import json
import random
import time

# Configure basic logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("ProgressiveTest")

def test_with_basic_headers():
    """Test with just a user agent"""
    url = "https://www.indeed.com/jobs?q=python+developer"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    logger.info("Testing with basic headers...")
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.select("div.job_seen_beacon")
            logger.info(f"Found {len(job_cards)} job cards")
            return True
        else:
            logger.error(f"Request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error during request: {e}")
        return False

def test_with_extended_headers():
    """Test with extended browser-like headers"""
    url = "https://www.indeed.com/jobs?q=python+developer"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5", 
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    logger.info("Testing with extended headers...")
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.select("div.job_seen_beacon")
            logger.info(f"Found {len(job_cards)} job cards")
            return True
        else:
            logger.error(f"Request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error during request: {e}")
        return False

def test_with_referer():
    """Test with all headers plus referer"""
    url = "https://www.indeed.com/jobs?q=python+developer"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5", 
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.google.com/"
    }
    
    logger.info("Testing with referer header...")
    try:
        response = requests.get(url, headers=headers)
        logger.info(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.select("div.job_seen_beacon")
            logger.info(f"Found {len(job_cards)} job cards")
            return True
        else:
            logger.error(f"Request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error during request: {e}")
        return False

def test_with_timing_variation():
    """Test with timing variations between requests"""
    url = "https://www.indeed.com/jobs?q=python+developer"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    logger.info("Testing with timing variations...")
    try:
        # Sleep a random time to mimic human behavior
        sleep_time = random.uniform(0.5, 2.5)
        logger.info(f"Sleeping for {sleep_time:.2f} seconds before request")
        time.sleep(sleep_time)
        
        response = requests.get(url, headers=headers)
        logger.info(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.select("div.job_seen_beacon")
            logger.info(f"Found {len(job_cards)} job cards")
            return True
        else:
            logger.error(f"Request failed with status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error during request: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting progressive tests...")
    
    results = {
        "basic_headers": test_with_basic_headers(),
        "extended_headers": test_with_extended_headers(),
        "with_referer": test_with_referer(),
        "timing_variation": test_with_timing_variation(),
    }
    
    logger.info("Test results summary:")
    for test_name, success in results.items():
        logger.info(f"{test_name}: {'✅ SUCCESS' if success else '❌ FAILED'}")