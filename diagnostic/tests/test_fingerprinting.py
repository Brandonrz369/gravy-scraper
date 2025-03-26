from bs4 import BeautifulSoup
import sys
import os
import logging

# Add parent directory to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import project modules
from protection_service import ProtectionService
from config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("FingerprintTest")

def test_fingerprinting_only():
    """Test with only fingerprinting enabled, no proxies"""
    # Initialize minimal components
    config_manager = ConfigManager()
    protection_service = ProtectionService(config_manager)
    
    # Disable everything except fingerprinting
    protection_service.set_enabled(True) 
    protection_service.fingerprinting = True
    protection_service.current_service = "Direct"  # No proxy, just fingerprinting
    
    # Test request with fingerprinting
    url = "https://www.indeed.com/jobs?q=python+developer"
    logger.info("Testing request with fingerprinting only (no proxy)...")
    html = protection_service.get_with_protection(url)
    
    # Process results
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.select("div.job_seen_beacon")
        logger.info(f"Found {len(job_cards)} job cards with fingerprinting enabled")
        return True
    else:
        logger.error("Request failed with fingerprinting enabled")
        return False

if __name__ == "__main__":
    logger.info("=== Starting Fingerprinting Test ===")
    success = test_fingerprinting_only()
    logger.info(f"Test result: {'SUCCESS' if success else 'FAILED'}")