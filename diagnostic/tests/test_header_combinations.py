import requests
import logging
import time
import sys
import os
from itertools import combinations

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("HeaderTest")

def test_individual_headers():
    """Test each header individually to find which ones trigger blocking"""
    # Base URL
    url = "https://www.indeed.com/jobs?q=python+developer"
    
    # Base headers that should work (minimal set)
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Advanced headers from protection_service
    advanced_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Referer": "https://www.google.com/"
    }
    
    # First test the baseline
    logger.info("Testing baseline with just User-Agent")
    try:
        response = requests.get(url, headers=base_headers)
        logger.info(f"Baseline status code: {response.status_code}")
        baseline_success = response.status_code == 200
    except Exception as e:
        logger.error(f"Baseline request failed: {e}")
        baseline_success = False
    
    if not baseline_success:
        logger.error("Baseline test failed, cannot continue with header tests")
        return False
    
    # Test each header individually
    results = {}
    for header, value in advanced_headers.items():
        test_headers = base_headers.copy()
        test_headers[header] = value
        
        logger.info(f"Testing with additional header: {header}")
        try:
            response = requests.get(url, headers=test_headers)
            status_code = response.status_code
            
            logger.info(f"Status code: {status_code}")
            success = status_code == 200
            results[header] = success
            
            if success:
                logger.info(f"Header {header} passed!")
            else:
                logger.error(f"Header {header} failed with status {status_code}")
        except Exception as e:
            logger.error(f"Request with header {header} failed with exception: {e}")
            results[header] = False
        
        # Avoid rate limiting
        time.sleep(5)
    
    # Test combinations of successful headers
    successful_headers = [h for h, s in results.items() if s]
    logger.info(f"Testing combinations of successful headers: {successful_headers}")
    
    if len(successful_headers) >= 2:
        for r in range(2, len(successful_headers) + 1):
            for combo in combinations(successful_headers, r):
                test_headers = base_headers.copy()
                for header in combo:
                    test_headers[header] = advanced_headers[header]
                
                combo_name = "+".join(combo)
                logger.info(f"Testing combination: {combo_name}")
                
                try:
                    response = requests.get(url, headers=test_headers)
                    status_code = response.status_code
                    
                    logger.info(f"Status code: {status_code}")
                    success = status_code == 200
                    results[combo_name] = success
                    
                    if success:
                        logger.info(f"Combination {combo_name} passed!")
                    else:
                        logger.error(f"Combination {combo_name} failed with status {status_code}")
                except Exception as e:
                    logger.error(f"Request with combination {combo_name} failed with exception: {e}")
                    results[combo_name] = False
                
                # Avoid rate limiting
                time.sleep(5)
    
    return results

if __name__ == "__main__":
    logger.info("=== Starting Header Combination Test ===")
    results = test_individual_headers()
    
    if results:
        logger.info("=== Test Results Summary ===")
        for header, success in results.items():
            logger.info(f"{header}: {'SUCCESS' if success else 'FAILED'}")
    else:
        logger.error("Tests could not be completed")