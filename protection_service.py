import time
import random
import logging
import requests
from urllib.parse import urlparse

class ProtectionService:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.enabled = config_manager.get_value("protection.enabled", True)
        self.fingerprinting = config_manager.get_value("protection.fingerprinting", True)
        self.current_service = config_manager.get_value("protection.current_service", "Direct")
        self.request_counts = {}
        self.max_requests_per_domain = 10
        self.logger = logging.getLogger("ProtectionService")
        
        # User agents for fingerprinting
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1"
        ]
    
    def set_enabled(self, enabled):
        """Enable or disable protection"""
        self.enabled = enabled
        self.config_manager.set_value("protection.enabled", enabled)
    
    def set_fingerprinting(self, enabled):
        """Enable or disable browser fingerprinting"""
        self.fingerprinting = enabled
        self.config_manager.set_value("protection.fingerprinting", enabled)
    
    def set_service(self, service_name):
        """Set the current proxy service"""
        self.current_service = service_name
        self.config_manager.set_value("protection.current_service", service_name)
    
    def configure_brightdata(self, username, password, host, port):
        """Configure BrightData proxy"""
        self.config_manager.set_value("protection.services.BrightData.enabled", True)
        self.config_manager.set_value("protection.services.BrightData.username", username)
        self.config_manager.set_value("protection.services.BrightData.password", password)
        self.config_manager.set_value("protection.services.BrightData.host", host)
        self.config_manager.set_value("protection.services.BrightData.port", port)
        self.set_service("BrightData")
        self.logger.info("BrightData proxy configured")
    
    def configure_scraperapi(self, api_key):
        """Configure ScraperAPI proxy"""
        self.config_manager.set_value("protection.services.ScraperAPI.enabled", True)
        self.config_manager.set_value("protection.services.ScraperAPI.api_key", api_key)
        self.set_service("ScraperAPI")
        self.logger.info("ScraperAPI proxy configured")
    
    def get_with_protection(self, url, headers=None):
        """Make a protected HTTP request"""
        if not self.enabled:
            return self._make_direct_request(url, headers)
        
        # Track requests per domain for rotation
        domain = self._extract_domain(url)
        if domain not in self.request_counts:
            self.request_counts[domain] = 0
        
        self.request_counts[domain] += 1
        
        # Rotate service if needed
        if self.request_counts[domain] > self.max_requests_per_domain:
            self._rotate_service()
            self.request_counts[domain] = 1
        
        # Prepare headers with fingerprinting if enabled
        request_headers = self._get_headers(headers)
        
        # Determine which service to use
        if self.current_service == "BrightData":
            return self._make_brightdata_request(url, request_headers)
        elif self.current_service == "ScraperAPI":
            return self._make_scraperapi_request(url, request_headers)
        else:
            return self._make_direct_request(url, request_headers)
    
    def _get_headers(self, custom_headers=None):
        """Get request headers with optional fingerprinting"""
        headers = {}
        
        if self.fingerprinting:
            # Add random User-Agent
            headers["User-Agent"] = random.choice(self.user_agents)
            
            # Add common headers for browser impersonation
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            headers["Accept-Language"] = "en-US,en;q=0.5"
            headers["Accept-Encoding"] = "gzip, deflate, br"
            headers["Connection"] = "keep-alive"
            headers["Upgrade-Insecure-Requests"] = "1"
            headers["Cache-Control"] = "max-age=0"
            
            # Add randomized referrer
            referrers = [
                "https://www.google.com/",
                "https://www.bing.com/",
                "https://www.yahoo.com/",
                "https://duckduckgo.com/"
            ]
            headers["Referer"] = random.choice(referrers)
        
        # Add custom headers if provided
        if custom_headers:
            headers.update(custom_headers)
        
        return headers
    
    def _extract_domain(self, url):
        """Extract domain from URL"""
        parsed_url = urlparse(url)
        return parsed_url.netloc
    
    def _rotate_service(self):
        """Rotate to next available service"""
        services = ["Direct"]
        
        # Add BrightData if configured
        if self.config_manager.get_value("protection.services.BrightData.enabled", False):
            services.append("BrightData")
        
        # Add ScraperAPI if configured
        if self.config_manager.get_value("protection.services.ScraperAPI.enabled", False):
            services.append("ScraperAPI")
        
        # Get current index and rotate to next
        try:
            current_index = services.index(self.current_service)
            next_index = (current_index + 1) % len(services)
            self.set_service(services[next_index])
            self.logger.info(f"Rotated to service: {self.current_service}")
        except ValueError:
            # Default to first service if current not found
            self.set_service(services[0])
            self.logger.info(f"Reset to service: {self.current_service}")
    
    def _make_brightdata_request(self, url, headers):
        """Make request through BrightData proxy"""
        # Get BrightData configuration
        username = self.config_manager.get_value("protection.services.BrightData.username", "")
        password = self.config_manager.get_value("protection.services.BrightData.password", "")
        host = self.config_manager.get_value("protection.services.BrightData.host", "")
        port = self.config_manager.get_value("protection.services.BrightData.port", "")
        
        if not all([username, password, host, port]):
            self.logger.warning("BrightData proxy not fully configured, falling back to direct request")
            return self._make_direct_request(url, headers)
        
        # Configure proxy
        proxy_url = f"http://{username}:{password}@{host}:{port}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        
        # Add jitter delay to appear more human-like
        time.sleep(random.uniform(1, 3))
        
        # Make request with retry logic
        max_retries = 3
        for retry in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    proxies=proxies, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code in [403, 429]:
                    # Being blocked, try another service next time
                    self.logger.warning(f"Blocked with status {response.status_code}, rotating service")
                    self._rotate_service()
                    time.sleep(2 ** retry)  # Exponential backoff
                else:
                    self.logger.warning(f"Unexpected status code: {response.status_code}")
                    return None
            except Exception as e:
                self.logger.error(f"Error making BrightData request: {e}")
                time.sleep(2 ** retry)  # Exponential backoff
        
        # All retries failed
        return None
    
    def _make_scraperapi_request(self, url, headers):
        """Make request through ScraperAPI"""
        # Get ScraperAPI configuration
        api_key = self.config_manager.get_value("protection.services.ScraperAPI.api_key", "")
        
        if not api_key:
            self.logger.warning("ScraperAPI not configured, falling back to direct request")
            return self._make_direct_request(url, headers)
        
        # Build ScraperAPI URL
        api_url = f"http://api.scraperapi.com?api_key={api_key}&url={url}"
        
        # Add jitter delay to appear more human-like
        time.sleep(random.uniform(1, 3))
        
        # Make request with retry logic
        max_retries = 3
        for retry in range(max_retries):
            try:
                response = requests.get(
                    api_url, 
                    headers=headers, 
                    timeout=60  # Longer timeout for proxy services
                )
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code in [403, 429]:
                    # Being blocked, try another service next time
                    self.logger.warning(f"Blocked with status {response.status_code}, rotating service")
                    self._rotate_service()
                    time.sleep(2 ** retry)  # Exponential backoff
                else:
                    self.logger.warning(f"Unexpected status code: {response.status_code}")
                    return None
            except Exception as e:
                self.logger.error(f"Error making ScraperAPI request: {e}")
                time.sleep(2 ** retry)  # Exponential backoff
        
        # All retries failed
        return None
    
    def _make_direct_request(self, url, headers):
        """Make direct request without proxy"""
        # Add jitter delay to appear more human-like
        time.sleep(random.uniform(0.5, 2))
        
        # Make request with retry logic
        max_retries = 3
        for retry in range(max_retries):
            try:
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=30
                )
                
                if response.status_code == 200:
                    return response.text
                elif response.status_code in [403, 429]:
                    self.logger.warning(f"Blocked with status {response.status_code}")
                    time.sleep(2 ** retry)  # Exponential backoff
                else:
                    self.logger.warning(f"Unexpected status code: {response.status_code}")
                    return None
            except Exception as e:
                self.logger.error(f"Error making direct request: {e}")
                time.sleep(2 ** retry)  # Exponential backoff
        
        # All retries failed
        return None