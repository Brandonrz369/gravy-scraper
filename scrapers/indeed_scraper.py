# scrapers/indeed_scraper.py - Indeed-specific scraper implementation
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote

class IndeedScraper:
    """Scraper for Indeed job listings"""
    
    def __init__(self):
        self.name = "Indeed"
        self.logger = logging.getLogger("IndeedScraper")
    
    def search(self, keywords, exclude_keywords, location, protection_service):
        """Search for jobs on Indeed"""
        self.logger.info(f"Searching Indeed for: {keywords}")
        
        # Build search URL
        keyword_str = " ".join(keywords)
        exclude_str = " ".join(f"-{kw}" for kw in exclude_keywords)
        
        query = f"{keyword_str} {exclude_str}".strip()
        encoded_query = quote(query)
        
        if location:
            encoded_location = quote(location)
            url = f"https://www.indeed.com/jobs?q={encoded_query}&l={encoded_location}"
        else:
            url = f"https://www.indeed.com/jobs?q={encoded_query}&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"
        
        # Get the page content
        # Get the page content
        html = protection_service.get_with_protection(url)
        
        if not html:
            self.logger.warning("Failed to get Indeed search results")
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
                job_id = ""
                
                if job_link_elem and job_link_elem.has_attr("href"):
                    job_path = job_link_elem["href"]
                    if job_path.startswith("/"):
                        job_url = f"https://www.indeed.com{job_path}"
                    else:
                        job_url = job_path
                    
                    # Extract job ID from URL
                    if "jk=" in job_url:
                        job_id = job_url.split("jk=")[1].split("&")[0]
                
                # Get job description snippet
                snippet_elem = card.select_one("div.job-snippet")
                
                # Get salary if available
                salary_elem = card.select_one("div.salary-snippet-container")
                
                # Create job object
                job = {
                    "id": job_id,
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
                self.logger.error(f"Error parsing Indeed job card: {e}")
        
        self.logger.info(f"Found {len(jobs)} jobs on Indeed")
        return jobs
    
    def get_job_details(self, job_url, protection_service):
        """Get full job details from job page"""
        if not job_url:
            return {}
        
        # Get the job page content
        html = protection_service.get_with_protection(job_url)
        
        if not html:
            self.logger.warning(f"Failed to get job details from {job_url}")
            return {}
        
        # Parse the HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract full job description
        description_elem = soup.select_one("div#jobDescriptionText")
        description = description_elem.text.strip() if description_elem else ""
        
        # Extract other details if available
        # (company info, benefits, etc.)
        
        return {
            "full_description": description
        }