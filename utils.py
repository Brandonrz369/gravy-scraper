# utils.py - Utility functions for the application
import re
import json
import os
import logging
from datetime import datetime
from urllib.parse import urlparse, urljoin

logger = logging.getLogger("GravyUtils")

def extract_price(price_str):
    """Extract numeric price from price string"""
    if not price_str:
        return 0
    
    # Extract digits and decimal point
    matches = re.findall(r'[\d,]+\.\d+|\d+', price_str)
    if matches:
        # Convert first match to float, removing commas
        return float(matches[0].replace(',', ''))
    
    return 0

def save_to_json(data, filename):
    """Save data to JSON file"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved data to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving data to {filename}: {e}")
        return False

def load_from_json(filename, default=None):
    """Load data from JSON file"""
    if not os.path.exists(filename):
        return default
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading data from {filename}: {e}")
        return default

def is_valid_url(url):
    """Check if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def make_absolute_url(base_url, relative_url):
    """Convert relative URL to absolute URL"""
    if not relative_url:
        return None
    
    if is_valid_url(relative_url):
        return relative_url
    
    return urljoin(base_url, relative_url)

def get_domain(url):
    """Extract domain from URL"""
    parsed_url = urlparse(url)
    return parsed_url.netloc

def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters"""
    return re.sub(r'[\\/*?:"<>|]', "", filename)

def timestamp():
    """Get current timestamp as string"""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def format_elapsed_time(seconds):
    """Format elapsed time in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"