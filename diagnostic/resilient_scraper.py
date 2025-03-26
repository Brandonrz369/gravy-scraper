"""
Resilient Scraper Module

Implements a multi-tiered approach to web scraping with fallback mechanisms
and adaptive header selection to maximize successful requests.
"""

import logging
import json
import os
import random
import requests
import time
import hashlib
from bs4 import BeautifulSoup
import sys

# Add parent directory to import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import project modules
from protection_service import ProtectionService
from config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ResilientScraper")

class AdaptiveHeaderSelector:
    """Tracks and selects headers based on their success rates"""
    
    def __init__(self, data_file='header_stats.json'):
        """Initialize with path to data file for persistent storage"""
        self.data_file = data_file
        self.header_success_rates = self._load_data()
        self.minimum_attempts = 5
        
        # Define baseline default headers
        self.DEFAULT_HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
    
    def _load_data(self):
        """Load header success data from file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading header stats: {e}")
        return {}
    
    def _save_data(self):
        """Save header success data to file"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.header_success_rates, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving header stats: {e}")
    
    def _headers_to_hash(self, headers):
        """Convert headers dict to a stable hash for storage"""
        headers_str = json.dumps(headers, sort_keys=True)
        return hashlib.md5(headers_str.encode()).hexdigest()
    
    def _hash_to_headers(self, headers_hash):
        """Convert a hash back to headers dict (requires lookup)"""
        for header_set in self.header_combos:
            if self._headers_to_hash(header_set) == headers_hash:
                return header_set
        return None
    
    def record_result(self, headers, success):
        """Record success/failure of a header combination"""
        headers_hash = self._headers_to_hash(headers)
        
        if headers_hash not in self.header_success_rates:
            self.header_success_rates[headers_hash] = {
                "headers": headers,  # Store the actual headers for lookup
                "success": 0, 
                "attempts": 0
            }
        
        self.header_success_rates[headers_hash]["attempts"] += 1
        if success:
            self.header_success_rates[headers_hash]["success"] += 1
            
        self._save_data()
    
    def get_best_headers(self):
        """Return header combination with highest success rate"""
        best_rate = 0
        best_headers = None
        
        for headers_hash, stats in self.header_success_rates.items():
            if stats["attempts"] < self.minimum_attempts:
                continue
                
            success_rate = stats["success"] / stats["attempts"]
            if success_rate > best_rate:
                best_rate = success_rate
                best_headers = stats["headers"]
                
        return best_headers or self.DEFAULT_HEADERS
    
    def get_header_variants(self):
        """Generate a list of header combinations to try"""
        variants = [
            # Minimal headers (baseline)
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
            # Basic browser headers
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            },
            # More complete browser headers
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            },
            # Complete browser headers with referrer
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Referer": "https://www.google.com/",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            }
        ]
        
        # Add the best headers we know about
        best_headers = self.get_best_headers()
        if best_headers not in variants:
            variants.append(best_headers)
            
        return variants

class ResilientScraper:
    """Multi-tiered web scraper with fallback mechanisms"""
    
    def __init__(self, config_manager=None):
        """Initialize with optional config manager"""
        if config_manager is None:
            config_manager = ConfigManager()
            
        self.config_manager = config_manager
        self.protection_service = ProtectionService(config_manager)
        self.header_selector = AdaptiveHeaderSelector()
        self.fallback_enabled = True
        
    def get_page(self, url):
        """Multi-tiered request strategy with fallbacks"""
        logger.info(f"Fetching URL: {url}")
        
        # Tier 1: Try with full protection if enabled
        if self.config_manager.get_value("protection.enabled", True):
            logger.info("Attempting with full protection layer")
            response = self._try_with_protection(url)
            if response:
                return response
            logger.warning("Protection layer approach failed")
                
        # Tier 2: If protection failed and fallbacks enabled, try header variants
        if self.fallback_enabled:
            logger.info("Falling back to adaptive header selection")
            return self._try_header_variants(url)
            
        logger.error("All request strategies failed")
        return None
        
    def _try_with_protection(self, url):
        """Attempt request with full protection layer"""
        try:
            html = self.protection_service.get_with_protection(url)
            success = html is not None
            
            # Record result for future reference
            headers = self._get_headers_from_protection_service()
            self.header_selector.record_result(headers, success)
            
            return html
        except Exception as e:
            logger.error(f"Protected request failed: {e}")
            return None
    
    def _get_headers_from_protection_service(self):
        """Extract the headers being used by protection service"""
        # This is a simplification - in reality we'd need to add logic
        # to extract the actual headers from the protection service
        if self.protection_service.fingerprinting:
            return {
                "User-Agent": random.choice(self.protection_service.user_agents),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
        else:
            return {"User-Agent": random.choice(self.protection_service.user_agents)}
            
    def _try_header_variants(self, url):
        """Try different header combinations based on past success"""
        variants = self.header_selector.get_header_variants()
        
        for headers in variants:
            logger.info(f"Trying variant: {list(headers.keys())}")
            
            try:
                # Add jitter delay to appear more human
                delay = random.uniform(1, 3)
                time.sleep(delay)
                
                response = requests.get(url, headers=headers, timeout=30)
                success = response.status_code == 200
                
                # Record this result
                self.header_selector.record_result(headers, success)
                
                if success:
                    logger.info(f"Request succeeded with variant {list(headers.keys())}")
                    return response.text
                else:
                    logger.warning(f"Request failed with variant {list(headers.keys())}: {response.status_code}")
            except Exception as e:
                logger.error(f"Request with variant {list(headers.keys())} failed: {e}")
                self.header_selector.record_result(headers, False)
        
        logger.error("All header variants failed")
        return None
    
    def search_jobs(self, query, location=None):
        """Search for jobs with the query (resilient implementation)"""
        # Build search URL
        if location:
            url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
        else:
            url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"
        
        # Get the page content
        html = self.get_page(url)
        
        if not html:
            logger.warning("Failed to get search results")
            return []
        
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract job listings
        job_cards = soup.select("div.job_seen_beacon")
        
        jobs = []
        for card in job_cards:
            try:
                # Extract job details
                title_elem = card.select_one("h2.jobTitle span")
                company_elem = card.select_one("span.companyName")
                location_elem = card.select_one("div.companyLocation")
                
                # Get job URL
                job_link_elem = card.select_one("h2.jobTitle a")
                job_url = ""
                
                if job_link_elem and job_link_elem.has_attr("href"):
                    job_path = job_link_elem["href"]
                    if job_path.startswith("/"):
                        job_url = f"https://www.indeed.com{job_path}"
                    else:
                        job_url = job_path
                
                # Get job description snippet
                snippet_elem = card.select_one("div.job-snippet")
                
                # Get salary if available
                salary_elem = card.select_one("div.salary-snippet-container")
                
                # Create job object
                job = {
                    "title": title_elem.text.strip() if title_elem else "Unknown",
                    "company": company_elem.text.strip() if company_elem else "Unknown",
                    "location": location_elem.text.strip() if location_elem else "Unknown",
                    "url": job_url,
                    "description": snippet_elem.text.strip() if snippet_elem else "",
                    "salary": salary_elem.text.strip() if salary_elem else "Not specified",
                    "source": "Indeed"
                }
                
                jobs.append(job)
            
            except Exception as e:
                logger.error(f"Error parsing job card: {e}")
        
        logger.info(f"Found {len(jobs)} jobs")
        return jobs

# Test the resilient scraper
if __name__ == "__main__":
    scraper = ResilientScraper()
    jobs = scraper.search_jobs("python developer")
    
    print(f"Found {len(jobs)} jobs")
    for i, job in enumerate(jobs[:5]):  # Show first 5 jobs
        print(f"\nJob {i+1}:")
        print(f"Title: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"URL: {job['url']}")
        print(f"Salary: {job['salary']}")
        print(f"Description: {job['description'][:100]}..." if len(job['description']) > 100 else f"Description: {job['description']}")