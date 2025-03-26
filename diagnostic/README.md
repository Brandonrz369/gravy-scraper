# Web Scraper Diagnostic Framework

This diagnostic framework helps identify and resolve issues with the Gravy Scraper application, specifically focusing on why job sites are blocking our requests.

## Overview

Job sites like Indeed and RemoteOK are actively blocking our scraper with 403 Forbidden responses. This diagnostic framework implements a systematic approach to:

1. Identify which components trigger blocking
2. Test different request patterns and headers
3. Develop a resilient architecture that can adapt to blocking measures

## Diagnostic Tests

### Running Tests

To run all diagnostic tests in sequence:
```bash
cd diagnostic/tests
python run_all_tests.py
```

The test results will be logged in the `logs/` directory with a summary in `diagnostic_results.log`.

### Test Descriptions

The diagnostic framework includes these tests:

1. **minimal_test.py** - Baseline test with minimal headers to confirm basic functionality
2. **progressive_test.py** - Tests different header configurations progressively
3. **test_fingerprinting.py** - Tests if browser fingerprinting is causing blocks
4. **test_protection_layer.py** - Tests the protection service layer
5. **test_header_combinations.py** - Methodically tests which header combinations trigger blocking
6. **test_request_timing.py** - Tests if request timing patterns affect success rates

## Resilient Scraper Implementation

The `resilient_scraper.py` implements a multi-tiered scraping approach:

1. Uses the protection service first when enabled
2. Falls back to adaptive header selection if protection fails
3. Tracks success rates of different header combinations
4. Learns over time which approach works best

### Key Components

1. `AdaptiveHeaderSelector` - Tracks and selects headers based on past success
2. `ResilientScraper` - Multi-tiered approach with fallbacks

## Interpretation of Results

After running the diagnostic tests, analyze the logs to identify:

1. Which headers or combination of headers trigger blocking
2. If request timing impacts success rates
3. Whether the protection service helps or hinders
4. Which approach has the highest success rate

Use these insights to adapt the main application accordingly.