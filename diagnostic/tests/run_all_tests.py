import logging
import os
import subprocess
import sys
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("diagnostic_results.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DiagnosticRunner")

def run_test(test_file):
    """Run a test file and return the result"""
    test_name = os.path.basename(test_file).replace('.py', '')
    
    logger.info(f"Running test: {test_name}")
    
    # Create log file for test output
    log_file = f"logs/{test_name}.log"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    try:
        # Run the test and capture output
        with open(log_file, 'w') as f:
            process = subprocess.run(
                [sys.executable, test_file],
                stdout=f,
                stderr=subprocess.STDOUT,
                check=False
            )
        
        success = process.returncode == 0
        logger.info(f"Test {test_name} completed with status: {'SUCCESS' if success else 'FAILED'}")
        
        # Add a brief summary from the log file
        with open(log_file, 'r') as f:
            log_content = f.read()
            
        # Look for key result indicators in the log
        if "SUCCESS" in log_content:
            logger.info(f"Test {test_name} reported success indicators")
        elif "FAILED" in log_content:
            logger.warning(f"Test {test_name} reported failure indicators")
            
        return {
            "name": test_name,
            "success": success,
            "log_file": log_file
        }
    except Exception as e:
        logger.error(f"Error running test {test_name}: {e}")
        return {
            "name": test_name,
            "success": False,
            "log_file": None,
            "error": str(e)
        }

def run_all_tests():
    """Run all diagnostic tests in sequence"""
    # Define test order - start with minimal tests, then progress to more complex ones
    test_files = [
        "minimal_test.py",
        "progressive_test.py",
        "test_fingerprinting.py",
        "test_protection_layer.py",
        "test_header_combinations.py",
        "test_request_timing.py"
    ]
    
    results = []
    
    # Ensure we're in the right directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    logger.info(f"Starting diagnostic test suite at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    for test_file in test_files:
        if not os.path.exists(test_file):
            logger.warning(f"Test file not found: {test_file}")
            continue
            
        result = run_test(test_file)
        results.append(result)
        
        # Add cooldown between tests to avoid rate limiting
        logger.info("Cooling down for 5 seconds before next test")
        time.sleep(5)
    
    logger.info("All tests completed")
    
    # Generate summary
    logger.info("=== Test Suite Summary ===")
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Tests passed: {success_count}/{len(results)}")
    
    for result in results:
        status = "✅ PASSED" if result["success"] else "❌ FAILED"
        logger.info(f"{result['name']}: {status}")
    
    return results

if __name__ == "__main__":
    run_all_tests()