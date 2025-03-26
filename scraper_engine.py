import json
import logging
import os
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

class ScraperEngine:
    def __init__(self, config_manager, claude_service, protection_service):
        self.config_manager = config_manager
        self.claude_service = claude_service
        self.protection_service = protection_service
        self.logger = logging.getLogger("ScraperEngine")
    
    def search_jobs(self, query, sources=None, location=None):
        """Search for jobs matching query"""
        self.logger.info(f"Searching for jobs: {query}")
        
        # API Call 1: Use Claude to analyze the query and generate search parameters
        # This API call is independent of VPN/fingerprinting settings
        search_params = self.claude_service.analyze_job_search(query)
        
        keywords = search_params.get("keywords", [query])
        exclude_keywords = search_params.get("exclude_keywords", [])
        
        self.logger.info(f"Generated keywords: {keywords}")
        self.logger.info(f"Generated exclude keywords: {exclude_keywords}")
        
        # Determine which sources to search
        if sources is None:
            sources = [
                source for source, enabled in 
                self.config_manager.get_value("job_sources", {}).items() 
                if enabled
            ]
        
        # Search each enabled source (Using VPN protection if enabled)
        all_jobs = []
        
        for source in sources:
            try:
                self.logger.info(f"Searching {source}...")
                if source == "Indeed":
                    jobs = self._search_indeed(keywords, exclude_keywords, location)
                elif source == "RemoteOK":
                    jobs = self._search_remoteok(keywords, exclude_keywords)
                elif source == "LinkedIn":
                    jobs = self._search_linkedin(keywords, exclude_keywords, location)
                elif source == "Freelancer":
                    jobs = self._search_freelancer(keywords, exclude_keywords)
                elif source == "Craigslist":
                    jobs = self._search_craigslist(keywords, exclude_keywords, location)
                else:
                    self.logger.warning(f"Unknown source: {source}")
                    continue
                
                self.logger.info(f"Found {len(jobs)} jobs on {source}")
                all_jobs.extend(jobs)
            except Exception as e:
                self.logger.error(f"Error searching {source}: {e}")
        
        # API Call 2: Filter out bootcamps and low-quality listings
        # This API call is independent of VPN/fingerprinting settings
        if all_jobs:
            filtered_jobs = self.claude_service.filter_jobs(all_jobs, query)
            self.logger.info(f"Filtered from {len(all_jobs)} to {len(filtered_jobs)} jobs")
            
            # Save to file
            self._save_jobs(filtered_jobs, "all_jobs.json")
            
            # Generate HTML report
            self._generate_job_report(filtered_jobs, query)
            
            return filtered_jobs
        else:
            self.logger.warning("No jobs found")
            return []
    
    def crawl_general(self, query, max_pages=10):
        """Execute a general crawl based on query"""
        self.logger.info(f"Starting general crawl: {query}")
        
        # API Call 3: Generate crawl strategy
        # This API call is independent of VPN/fingerprinting settings
        strategy = self.claude_service.analyze_general_query(query)
        
        target_sites = strategy.get("target_sites", [])
        search_params = strategy.get("search_parameters", {})
        data_points = strategy.get("data_points", [])
        filtering_criteria = strategy.get("filtering_criteria", {})
        
        self.logger.info(f"Generated strategy for {len(target_sites)} sites: {target_sites}")
        
        # Generate search URLs
        search_urls = self._generate_search_urls(target_sites, search_params)
        
        # Crawl each URL (Using VPN protection if enabled)
        all_results = []
        
        for url in search_urls:
            try:
                self.logger.info(f"Crawling: {url}")
                
                # Make request with protection
                html = self.protection_service.get_with_protection(url)
                
                if html:
                    # Extract data from the page
                    page_results = self._extract_data(html, url, data_points)
                    
                    if page_results:
                        self.logger.info(f"Found {len(page_results)} results from {url}")
                        all_results.extend(page_results)
                        
                        # Find and follow next page if within limit
                        current_page = 1
                        while current_page < max_pages:
                            next_url = self._find_next_page(html, url)
                            if not next_url or next_url == url:
                                break
                                
                            # Request next page
                            self.logger.info(f"Following next page: {next_url}")
                            html = self.protection_service.get_with_protection(next_url)
                            if not html:
                                break
                                
                            # Extract data from next page
                            next_results = self._extract_data(html, next_url, data_points)
                            if next_results:
                                self.logger.info(f"Found {len(next_results)} results on page {current_page + 1}")
                                all_results.extend(next_results)
                                
                                # Update for next iteration
                                url = next_url
                                current_page += 1
                            else:
                                break
                    else:
                        self.logger.warning(f"No results extracted from {url}")
                else:
                    self.logger.warning(f"Failed to get content from {url}")
            except Exception as e:
                self.logger.error(f"Error crawling {url}: {e}")
        
        # Apply filtering criteria
        filtered_results = self._apply_filters(all_results, filtering_criteria)
        self.logger.info(f"Filtered from {len(all_results)} to {len(filtered_results)} results")
        
        # Save results and generate report
        if filtered_results:
            with open("crawl_results.json", "w") as f:
                json.dump(filtered_results, f, indent=2)
            
            self._generate_crawl_report(filtered_results, query)
            
            return filtered_results
        else:
            self.logger.warning("No results found")
            return []
    
    def _search_indeed(self, keywords, exclude_keywords, location=None):
        """Search Indeed for jobs"""
        # Build search URL
        keyword_str = "+".join(keywords)
        exclude_str = " ".join(f"-{kw}" for kw in exclude_keywords)
        
        query = f"{keyword_str} {exclude_str}".strip()
        query = query.replace(" ", "+")
        
        if location:
            url = f"https://www.indeed.com/jobs?q={query}&l={location}"
        else:
            url = f"https://www.indeed.com/jobs?q={query}&remotejob=032b3046-06a3-4876-8dfd-474eb5e7ed11"
        
        # Get the page content
        html = self.protection_service.get_with_protection(url)
        
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
                self.logger.error(f"Error parsing Indeed job card: {e}")
        
        return jobs
    
    def _search_remoteok(self, keywords, exclude_keywords):
        """Search RemoteOK for jobs"""
        # Simplified implementation - expand as needed
        keyword_str = "+".join(keywords)
        url = f"https://remoteok.com/remote-{keyword_str}-jobs"
        
        html = self.protection_service.get_with_protection(url)
        
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
                job_url = "https://remoteok.com" + row.get("data-url", "") if row.has_attr("data-url") else ""
                
                # Get job description
                desc_elem = row.select_one("div.description")
                
                # Get salary if available
                salary_elem = row.select_one("div.salary")
                
                # Create job object
                job = {
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
                self.logger.error(f"Error parsing RemoteOK job card: {e}")
        
        return jobs
    
    def _search_linkedin(self, keywords, exclude_keywords, location=None):
        """Search LinkedIn for jobs"""
        # LinkedIn has strong anti-scraping measures, so this is a placeholder implementation
        # In a production environment, you would need to use their API or implement more sophisticated scraping
        self.logger.warning("LinkedIn scraping not fully implemented - this is a placeholder")
        return []
    
    def _search_freelancer(self, keywords, exclude_keywords):
        """Search Freelancer for jobs"""
        # Placeholder implementation
        self.logger.warning("Freelancer scraping not fully implemented - this is a placeholder")
        return []
    
    def _search_craigslist(self, keywords, exclude_keywords, location=None):
        """Search Craigslist for jobs"""
        # Craigslist implementation would depend on location
        # This is a placeholder implementation
        self.logger.warning("Craigslist scraping not fully implemented - this is a placeholder")
        return []
    
    def _generate_search_urls(self, target_sites, search_params):
        """Generate search URLs for target sites"""
        urls = []
        
        # Get search keywords
        keywords = search_params.get("keywords", [])
        keyword_str = "+".join(keywords)
        
        # Generate URLs for each target site
        for site in target_sites:
            if "ebay.com" in site:
                # eBay URL construction
                price_min = search_params.get("filters", {}).get("price_min", "")
                price_max = search_params.get("filters", {}).get("price_max", "")
                
                url = f"https://www.ebay.com/sch/i.html?_nkw={keyword_str}"
                if price_min:
                    url += f"&_udlo={price_min}"
                if price_max:
                    url += f"&_udhi={price_max}"
                
                urls.append(url)
            
            elif "amazon.com" in site:
                # Amazon URL construction
                url = f"https://www.amazon.com/s?k={keyword_str}"
                urls.append(url)
            
            elif "google.com" in site:
                # Google URL construction
                url = f"https://www.google.com/search?q={keyword_str}"
                urls.append(url)
            
            elif "kayak.com" in site:
                # Kayak URL construction (for flight searches)
                origin = search_params.get("filters", {}).get("origin", "")
                destination = search_params.get("filters", {}).get("destination", "")
                date = search_params.get("filters", {}).get("date", "")
                
                if origin and destination:
                    url = f"https://www.kayak.com/flights/{origin}-{destination}"
                    if date:
                        url += f"/{date}"
                    urls.append(url)
            
            else:
                # Generic URL construction
                url = f"https://{site}/search?q={keyword_str}"
                urls.append(url)
        
        return urls
    
    def _extract_data(self, html, url, data_points):
        """Extract data from HTML based on the URL and data points"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Determine extraction logic based on the domain
        domain = urlparse(url).netloc
        
        if "ebay.com" in domain:
            # eBay extraction logic
            items = soup.select('li.s-item')
            for item in items:
                try:
                    title_elem = item.select_one('h3.s-item__title')
                    price_elem = item.select_one('span.s-item__price')
                    link_elem = item.select_one('a.s-item__link')
                    
                    result = {
                        "title": title_elem.text.strip() if title_elem else "",
                        "price": price_elem.text.strip() if price_elem else "",
                        "url": link_elem['href'] if link_elem and 'href' in link_elem.attrs else "",
                        "source": "ebay.com"
                    }
                    
                    # Extract additional data points if requested
                    if "condition" in data_points:
                        condition_elem = item.select_one('span.SECONDARY_INFO')
                        if condition_elem:
                            result["condition"] = condition_elem.text.strip()
                    
                    if "shipping" in data_points:
                        shipping_elem = item.select_one('span.s-item__shipping')
                        if shipping_elem:
                            result["shipping"] = shipping_elem.text.strip()
                    
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error extracting eBay item: {e}")
        
        elif "amazon.com" in domain:
            # Amazon extraction logic
            items = soup.select('div[data-component-type="s-search-result"]')
            for item in items:
                try:
                    title_elem = item.select_one('h2 span')
                    price_elem = item.select_one('span.a-price .a-offscreen')
                    link_elem = item.select_one('h2 a')
                    
                    result = {
                        "title": title_elem.text.strip() if title_elem else "",
                        "price": price_elem.text.strip() if price_elem else "",
                        "url": f"https://www.amazon.com{link_elem['href']}" if link_elem and 'href' in link_elem.attrs else "",
                        "source": "amazon.com"
                    }
                    
                    # Extract additional data points if requested
                    if "rating" in data_points:
                        rating_elem = item.select_one('span.a-icon-alt')
                        if rating_elem:
                            result["rating"] = rating_elem.text.strip()
                    
                    if "review_count" in data_points:
                        review_elem = item.select_one('span.a-size-base')
                        if review_elem:
                            result["review_count"] = review_elem.text.strip()
                    
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error extracting Amazon item: {e}")
        
        elif "kayak.com" in domain:
            # Kayak flights extraction
            items = soup.select('div[class*="resultInner"]')
            for item in items:
                try:
                    price_elem = item.select_one('span[class*="price-text"]')
                    airline_elem = item.select_one('div[class*="carrierName"]')
                    time_elem = item.select_one('div[class*="duration"]')
                    
                    result = {
                        "price": price_elem.text.strip() if price_elem else "",
                        "airline": airline_elem.text.strip() if airline_elem else "",
                        "duration": time_elem.text.strip() if time_elem else "",
                        "source": "kayak.com"
                    }
                    
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error extracting Kayak flight: {e}")
        
        else:
            # Generic extraction logic - try to find product-like items
            items = soup.select('div.product, div.item, div.result, div[class*="product"], div[class*="item"]')
            for item in items:
                try:
                    title_elem = item.select_one('h2, h3, h4, [class*="title"]')
                    price_elem = item.select_one('[class*="price"]')
                    link_elem = item.select_one('a')
                    
                    result = {
                        "title": title_elem.text.strip() if title_elem else "",
                        "price": price_elem.text.strip() if price_elem else "",
                        "url": link_elem['href'] if link_elem and 'href' in link_elem.attrs else "",
                        "source": domain
                    }
                    
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Error extracting generic item: {e}")
        
        return results
    
    def _find_next_page(self, html, url):
        """Find next page URL in HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        domain = urlparse(url).netloc
        next_url = None
        
        # Site-specific next page selectors
        if "ebay.com" in domain:
            next_elem = soup.select_one('a.pagination__next')
            if next_elem and 'href' in next_elem.attrs:
                next_url = next_elem['href']
        
        elif "amazon.com" in domain:
            next_elem = soup.select_one('a.s-pagination-next')
            if next_elem and 'href' in next_elem.attrs:
                next_url = urljoin("https://www.amazon.com", next_elem['href'])
        
        else:
            # Generic next page detection
            next_patterns = [
                'a[rel="next"]', 
                'a.next', 
                'a.pagination-next', 
                'a[aria-label="Next"]',
                'a[aria-label="Next page"]',
                'a.pagination__next',
                'a.s-pagination-next',
                'a[class*="next"]',
                'a:contains("Next")'
            ]
                
            for pattern in next_patterns:
                next_elem = soup.select_one(pattern)
                if next_elem and 'href' in next_elem.attrs:
                    next_url = next_elem['href']
                    break
        
        # Make relative URLs absolute
        if next_url and not next_url.startswith(('http://', 'https://')):
            next_url = urljoin(url, next_url)
        
        return next_url
    
    def _apply_filters(self, results, filtering_criteria):
        """Apply filtering criteria to results"""
        if not filtering_criteria or not results:
            return results
        
        filtered_results = results.copy()
        
        # Price below filter
        if "price_below" in filtering_criteria:
            price_max = filtering_criteria["price_below"]
            filtered_results = [
                r for r in filtered_results 
                if self._extract_price(r.get("price", "")) <= price_max
            ]
        
        # Price above filter
        if "price_above" in filtering_criteria:
            price_min = filtering_criteria["price_above"]
            filtered_results = [
                r for r in filtered_results 
                if self._extract_price(r.get("price", "")) >= price_min
            ]
        
        # Must include terms filter
        if "must_include_terms" in filtering_criteria:
            terms = filtering_criteria["must_include_terms"]
            filtered_results = [
                r for r in filtered_results 
                if any(term.lower() in r.get("title", "").lower() for term in terms)
            ]
        
        # Exclude terms filter
        if "exclude_terms" in filtering_criteria:
            terms = filtering_criteria["exclude_terms"]
            filtered_results = [
                r for r in filtered_results 
                if not any(term.lower() in r.get("title", "").lower() for term in terms)
            ]
        
        return filtered_results
    
    def _extract_price(self, price_str):
        """Extract numeric price from price string"""
        import re
        
        if not price_str:
            return 0
        
        # Extract digits and decimal point
        matches = re.findall(r'[\d,]+\.\d+|\d+', price_str)
        if matches:
            # Convert first match to float, removing commas
            return float(matches[0].replace(',', ''))
        
        return 0
    
    def _save_jobs(self, jobs, filename):
        """Save jobs to JSON file"""
        try:
            with open(filename, "w") as f:
                json.dump(jobs, f, indent=2)
            
            self.logger.info(f"Saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving jobs to {filename}: {e}")
    
    def _generate_job_report(self, jobs, query):
        """Generate HTML report for job listings"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Job Search Results - {query}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
                .job-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
                .job-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 5px; color: #2c3e50; }}
                .job-company {{ font-weight: bold; color: #3498db; }}
                .job-location {{ color: #7f8c8d; }}
                .job-salary {{ color: #27ae60; font-weight: bold; }}
                .job-source {{ display: inline-block; padding: 3px 8px; border-radius: 3px; 
                            font-size: 0.8em; background-color: #eee; margin: 5px 0; }}
                .job-description {{ margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px; }}
                .job-link {{ display: inline-block; margin-top: 10px; color: #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Job Search Results for: {query}</h1>
                <p>Found {len(jobs)} matching jobs</p>
        """
        
        for job in jobs:
            html += f"""
                <div class="job-card">
                    <div class="job-title">{job.get('title', 'Unknown')}</div>
                    <div class="job-company">{job.get('company', 'Unknown')}</div>
                    <div class="job-location">{job.get('location', 'Unknown')}</div>
            """
            
            # Add salary if available
            if job.get('salary') and job.get('salary') != "Not specified":
                html += f'<div class="job-salary">{job.get("salary")}</div>'
            
            html += f'<div class="job-source">{job.get("source", "Unknown")}</div>'
            
            # Add description if available
            if job.get('description'):
                html += f'<div class="job-description">{job.get("description")}</div>'
            
            # Add link if available
            if job.get('url'):
                html += f'<a href="{job.get("url")}" target="_blank" class="job-link">View Job</a>'
            
            html += """
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        with open("gravy_jobs.html", "w") as f:
            f.write(html)
        
        self.logger.info("Generated job report: gravy_jobs.html")
    
    def _generate_crawl_report(self, results, query):
        """Generate HTML report for general crawl results"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Crawl Results - {query}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
                .item-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; }}
                .item-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 5px; color: #2c3e50; }}
                .item-price {{ color: #27ae60; font-weight: bold; }}
                .item-source {{ display: inline-block; padding: 3px 8px; border-radius: 3px; 
                             font-size: 0.8em; background-color: #eee; margin: 5px 0; }}
                .item-link {{ display: inline-block; margin-top: 10px; color: #3498db; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Crawl Results for: {query}</h1>
                <p>Found {len(results)} matching results</p>
        """
        
        for item in results:
            html += f"""
                <div class="item-card">
                    <div class="item-title">{item.get('title', 'Unknown')}</div>
            """
            
            # Add price if available
            if item.get('price'):
                html += f'<div class="item-price">{item.get("price")}</div>'
            
            html += f'<div class="item-source">{item.get("source", "Unknown")}</div>'
            
            # Add additional fields
            for key, value in item.items():
                if key not in ['title', 'price', 'url', 'source'] and value:
                    html += f'<div class="item-{key}">{key.capitalize()}: {value}</div>'
            
            # Add link if available
            if item.get('url'):
                html += f'<a href="{item.get("url")}" target="_blank" class="item-link">View Item</a>'
            
            html += """
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        with open("gravy_crawler.html", "w") as f:
            f.write(html)
        
        self.logger.info("Generated crawl report: gravy_crawler.html")