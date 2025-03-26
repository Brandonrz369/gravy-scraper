import json
import requests
import logging

class ClaudeService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.api_key = config_manager.get_value("claude_api.api_key", "")
        self.model = config_manager.get_value("claude_api.model", "claude-3-opus-20240229")
        self.endpoint = "https://api.anthropic.com/v1/messages"
        self.logger = logging.getLogger("ClaudeService")
    
    def configure(self, api_key, model="claude-3-opus-20240229"):
        """Configure the Claude API"""
        self.api_key = api_key
        self.model = model
        self.config_manager.set_value("claude_api.api_key", api_key)
        self.config_manager.set_value("claude_api.model", model)
    
    def get_completion(self, prompt, max_tokens=4000, system_prompt=None, response_format=None):
        """Get completion from Claude API - independent of VPN settings"""
        if not self.api_key:
            self.logger.warning("No Claude API key configured")
            return "Error: Claude API not configured"
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        if system_prompt:
            data["system"] = system_prompt
            
        if response_format:
            data["response_format"] = response_format
        
        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=data
            )
            
            if response.status_code != 200:
                self.logger.error(f"Claude API error: {response.status_code} - {response.text}")
                return f"Error: {response.status_code} - {response.text}"
            
            return response.json()["content"][0]["text"]
        except Exception as e:
            self.logger.error(f"Error calling Claude API: {e}")
            return f"Error: {e}"
    
    # API CALL NODE 1: Dynamic Template Generation
    def generate_search_template(self, job_category):
        """Dynamically generate a custom search template based on job category"""
        prompt = f"""
        Create a custom job search template for the category: "{job_category}"
        
        I need a natural language query that would help find jobs in this category.
        The template should be specific, targeted, and include key terms relevant to this field.
        
        Respond ONLY with the template text itself, nothing else.
        """
        
        try:
            template = self.get_completion(prompt, max_tokens=200)
            return template.strip()
        except Exception as e:
            self.logger.error(f"Error generating search template: {e}")
            return f"Find jobs related to {job_category}"
    
    # API CALL NODE 2: Job Search Parameter Generation
    def analyze_job_search(self, query):
        """Generate job search parameters from natural language query - independent API call"""
        prompt = f"""
        I need optimized search parameters for finding this kind of job: "{query}"
        
        Please provide:
        1. Keywords that would help find relevant job listings
        2. Keywords to exclude to filter out irrelevant listings
        
        Respond ONLY with a JSON object in this format:
        {{
            "keywords": ["keyword1", "keyword2", ...],
            "exclude_keywords": ["exclude1", "exclude2", ...]
        }}
        """
        
        try:
            response = self.get_completion(
                prompt, 
                response_format={"type": "json"}
            )
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Error analyzing job search: {e}")
            return {"keywords": [query], "exclude_keywords": []}
    
    # API CALL NODE 3: Job Result Filtering
    def filter_jobs(self, jobs, query):
        """Filter jobs to remove bootcamps and low-quality listings - independent API call"""
        if not jobs:
            return []
            
        # Prepare sample of jobs for analysis
        sample = jobs[:20]  # Limit to 20 to avoid token limits
        job_samples = []
        for i, job in enumerate(sample):
            job_samples.append({
                "id": i,
                "title": job.get("title", ""),
                "company": job.get("company", ""),
                "description": job.get("description", "")[:300] if job.get("description") else ""
            })
        
        prompt = f"""
        Analyze these job listings found for the search "{query}".
        
        Filter out:
        1. Coding bootcamps or training programs disguised as jobs
        2. Obvious spam or scam listings
        3. Extremely low-quality listings with no information
        4. Listings that don't match what the user is looking for
        
        Job listings:
        {job_samples}
        
        For each job, provide:
        - "keep" (true/false)
        - "reason" (brief explanation)
        
        Respond ONLY with a JSON array in this format:
        [
            {{"id": 0, "keep": true, "reason": "..."}},
            {{"id": 1, "keep": false, "reason": "..."}}
        ]
        """
        
        try:
            response = self.get_completion(
                prompt,
                response_format={"type": "json"}
            )
            
            decisions = json.loads(response)
            keep_map = {d["id"]: d["keep"] for d in decisions}
            
            # Filter the jobs
            filtered_jobs = []
            for i, job in enumerate(jobs):
                if i >= 20 or keep_map.get(i, True):  # Keep all jobs beyond analyzed samples
                    filtered_jobs.append(job)
            
            return filtered_jobs
        except Exception as e:
            self.logger.error(f"Error filtering jobs: {e}")
            return jobs  # On error, return all jobs
    
    # API CALL NODE 4: General Crawl Strategy
    def analyze_general_query(self, query):
        """Analyze a general query for the crawl strategy - independent API call"""
        prompt = f"""
        I need to crawl websites based on this query: "{query}"
        
        Please analyze this query and provide:
        1. Target websites to search
        2. Search parameters and keywords
        3. Data points to extract
        4. Filtering criteria
        
        Respond ONLY with a JSON object in this format:
        {{
            "target_sites": ["site1.com", "site2.com"],
            "search_parameters": {{
                "keywords": ["keyword1", "keyword2"],
                "filters": {{"price_max": 200}}
            }},
            "data_points": ["title", "price", "description"],
            "filtering_criteria": {{
                "price_below": 200,
                "must_include_terms": ["term1", "term2"]
            }}
        }}
        """
        
        try:
            response = self.get_completion(
                prompt,
                response_format={"type": "json"}
            )
            return json.loads(response)
        except Exception as e:
            self.logger.error(f"Error analyzing general query: {e}")
            # Return basic strategy as fallback
            return {
                "target_sites": self._extract_sites_from_query(query),
                "search_parameters": {"keywords": [query]},
                "data_points": ["title", "price", "description"],
                "filtering_criteria": {}
            }
    
    def _extract_sites_from_query(self, query):
        """Simple extraction of site names from query"""
        common_sites = ["ebay", "amazon", "google", "expedia", "kayak", "airbnb", "walmart", "target"]
        sites = []
        for site in common_sites:
            if site.lower() in query.lower():
                sites.append(f"{site}.com")
        return sites if sites else ["google.com"]