# scrapers/remoteok_scraper.py - RemoteOK-specific scraper implementation
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote

class RemoteOKScraper:
    """Scraper for RemoteOK job listings"""
    
    def __init__(self):
        self.name = "RemoteOK"
        self.logger = logging.getLogger("RemoteOKScraper")
    
    def search(self, keywords, exclude_keywords, location, protection_service):
        """Search for jobs on RemoteOK"""
        self.logger.info(f"Searching RemoteOK for: {keywords}")
        
        # Build search URL - RemoteOK uses simple tag-based URLs
        keyword_str = "-".join(keywords)
        url = f"https://remoteok.com/remote-{keyword_str}-jobs"
        
        # Get the page content
        html = protection_service.get_with_protection(url)
        
        if not html:
            self.logger.warning("Failed to get RemoteOK search results")
            return []
        
        # Parse HTML and extract jobs
        soup = BeautifulSoup(html, 'html.parser')
        job_rows = soup.select("tr.job")
        
        jobs = []
        for row in job_rows:
            try:
                # Extract job details
                title_elem = row.select_one("h2")
                company_elem = row.select_one("h3")
                tags_elem = row.select("div.tags div.tag")
                
                # Get job URL
                job_id = row.get("data-id", "")
                job_url = f"https://remoteok.com/l/{job_id}" if job_id else ""
                
                # Get job description
                desc_elem = row.select_one("div.description")
                
                # Get salary if available
                salary_elem = row.select_one("div.salary")
                
                # Create job object
                job = {
                    "id": job_id,
                    "title": title_elem.text.strip() if title_elem else "Unknown",
                    "company": company_elem.text.strip() if company_elem else "Unknown",
                    "location": "Remote",
                    "url": job_url,
                    "description": desc_elem.text.strip() if desc_elem else "",
                    "salary": salary_elem.text.strip() if salary_elem else "Not specified",
                    "tags": [tag.text.strip() for tag in tags_elem] if tags_elem else [],
                    "source": "RemoteOK"
                }
                
                # Filter out jobs with exclude keywords in title or description
                if any(kw.lower() in job["title"].lower() or 
                       kw.lower() in job["description"].lower() 
                       for kw in exclude_keywords):
                    continue
                
                jobs.append(job)
            
            except Exception as e:
                self.logger.error(f"Error parsing RemoteOK job row: {e}")
        
        self.logger.info(f"Found {len(jobs)} jobs on RemoteOK")
        return jobs