import json
import os
import logging

class ConfigManager:
    DEFAULT_CONFIG = {
        "license": {
            "key": "",
            "valid_until": "",
            "enabled_features": []
        },
        "claude_api": {
            "api_key": "",
            "model": "claude-3-opus-20240229"
        },
        "protection": {
            "enabled": True,
            "fingerprinting": True,
            "current_service": "Direct",
            "services": {
                "BrightData": {
                    "enabled": False,
                    "username": "",
                    "password": "",
                    "host": "",
                    "port": ""
                },
                "ScraperAPI": {
                    "enabled": False,
                    "api_key": ""
                }
            }
        },
        "job_sources": {
            "Indeed": True,
            "RemoteOK": True,
            "LinkedIn": True, 
            "Freelancer": True,
            "Craigslist": True
        }
    }
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self):
        """Load config from file or create default if it doesn't exist"""
        if not os.path.exists(self.config_path):
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
        
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config):
        """Save config to file"""
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def get_value(self, path, default=None):
        """Get value from config using dot notation path"""
        parts = path.split(".")
        current = self.config
        
        for part in parts:
            if part not in current:
                return default
            current = current[part]
        
        return current
    
    def set_value(self, path, value):
        """Set value in config using dot notation path"""
        parts = path.split(".")
        current = self.config
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
        self._save_config(self.config)
    
    def validate_license(self, license_key):
        """Simple license validation"""
        # In a real implementation, this would validate against a server
        valid_keys = {
            "GRAVY-PREMIUM-1234": {
                "valid_until": "2026-03-25T11:57:11.977976",
                "enabled_features": [
                    "basic_scraping", 
                    "commercial_proxies", 
                    "advanced_scraping", 
                    "claude_integration", 
                    "general_scraping"
                ]
            }
        }
        
        if license_key in valid_keys:
            # Set license details in config
            self.set_value("license.key", license_key)
            self.set_value("license.valid_until", valid_keys[license_key]["valid_until"])
            self.set_value("license.enabled_features", valid_keys[license_key]["enabled_features"])
            return True, valid_keys[license_key]
        else:
            return False, {}