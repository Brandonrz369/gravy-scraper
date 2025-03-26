import requests
import logging
import time
import random
import sys
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("TimingTest")

def test_timing_patterns():
    """Test different request timing patterns to see which ones avoid blocking"""
    url = "https://www.indeed.com/jobs?q=python+developer"
    
    # Use minimal headers that have been verified to work
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Define timing patterns to test
    patterns = [
        {"name": "Fixed delay (2s)", "func": lambda i: 2},
        {"name": "Random delay (1-3s)", "func": lambda i: random.uniform(1, 3)},
        {"name": "Random delay (0.5-2s)", "func": lambda i: random.uniform(0.5, 2)},
        {"name": "Exponential backoff", "func": lambda i: 1 + (0.5 * i)},
        {"name": "Variable humanlike", "func": lambda i: random.normalvariate(2, 0.5)}
    ]
    
    results = {}
    
    for pattern in patterns:
        success_count = 0
        attempts = 5
        
        logger.info(f"Testing timing pattern: {pattern['name']}")
        
        for i in range(attempts):
            # Apply delay according to pattern
            delay = pattern["func"](i)
            delay = max(0.1, delay)  # Ensure positive delay
            
            logger.info(f"Attempt {i+1}: Waiting {delay:.2f}s before request")
            time.sleep(delay)
            
            # Make request
            try:
                response = requests.get(url, headers=headers)
                status_code = response.status_code
                
                if status_code == 200:
                    success_count += 1
                    logger.info(f"Attempt {i+1}: Success (status: {status_code})")
                else:
                    logger.error(f"Attempt {i+1}: Failed with status {status_code}")
            except Exception as e:
                logger.error(f"Attempt {i+1}: Failed with exception: {e}")
        
        success_rate = success_count / attempts
        results[pattern["name"]] = {
            "success_count": success_count,
            "attempts": attempts,
            "success_rate": success_rate
        }
        
        logger.info(f"Pattern {pattern['name']}: {success_count}/{attempts} successful requests ({success_rate*100:.0f}%)")
        
        # Cooldown between patterns to avoid overall rate limiting
        logger.info(f"Cooling down for 10 seconds before next pattern")
        time.sleep(10)
    
    return results

if __name__ == "__main__":
    logger.info("=== Starting Request Timing Test ===")
    results = test_timing_patterns()
    
    logger.info("=== Test Results Summary ===")
    for pattern_name, stats in results.items():
        logger.info(f"{pattern_name}: {stats['success_count']}/{stats['attempts']} successful ({stats['success_rate']*100:.0f}%)")