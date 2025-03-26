import logging
import os
import sys

def setup_logging():
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("gravy_scraper.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function"""
    # Set up logging
    setup_logging()
    
    logger = logging.getLogger("GravyScraper")
    logger.info("Starting Gravy Scraper Application")
    
    try:
        # Import components here to avoid circular imports
        from config_manager import ConfigManager
        from claude_service import ClaudeService
        from protection_service import ProtectionService
        from scraper_engine import ScraperEngine
        from gui import GravyScraperApp
        
        # Create components
        config_manager = ConfigManager()
        claude_service = ClaudeService(config_manager)
        protection_service = ProtectionService(config_manager)
        scraper_engine = ScraperEngine(config_manager, claude_service, protection_service)
        
        # Create and run the GUI
        app = GravyScraperApp(config_manager, claude_service, protection_service, scraper_engine)
        app.run()
    
    except Exception as e:
        logger.error(f"Error in main application: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()