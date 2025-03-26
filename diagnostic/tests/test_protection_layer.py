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
logger = logging.getLogger("ProtectionLayerTest")

def test_protection_layer():
    """Test the protection layer with direct connection (no proxy)"""
    # Initialize minimal components
    config_manager = ConfigManager()
    protection_service = ProtectionService(config_manager)
    
    # Enable protection but use direct connection
    protection_service.set_enabled(True)
    protection_service.set_service("Direct")
    
    # First, test with fingerprinting disabled
    protection_service.set_fingerprinting(False)
    
    # Test request through protection layer without fingerprinting
    url = "https://www.indeed.com/jobs?q=python+developer"
    logger.info("Testing protection layer without fingerprinting...")
    html = protection_service.get_with_protection(url)
    
    # Process results
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.select("div.job_seen_beacon")
        logger.info(f"Found {len(job_cards)} job cards through protection layer (no fingerprinting)")
        result1 = True
    else:
        logger.error("Protection layer request failed without fingerprinting")
        result1 = False
    
    # Now test with fingerprinting enabled
    protection_service.set_fingerprinting(True)
    
    logger.info("Testing protection layer with fingerprinting...")
    html = protection_service.get_with_protection(url)
    
    # Process results
    if html:
        soup = BeautifulSoup(html, 'html.parser')
        job_cards = soup.select("div.job_seen_beacon")
        logger.info(f"Found {len(job_cards)} job cards through protection layer (with fingerprinting)")
        result2 = True
    else:
        logger.error("Protection layer request failed with fingerprinting")
        result2 = False
    
    return {
        "without_fingerprinting": result1,
        "with_fingerprinting": result2
    }

if __name__ == "__main__":
    logger.info("=== Starting Protection Layer Test ===")
    results = test_protection_layer()
    
    logger.info("=== Test Results ===")
    for test_name, success in results.items():
        logger.info(f"{test_name}: {'SUCCESS' if success else 'FAILED'}")