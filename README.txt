# Gravy Scraper

A powerful job scraping and general web crawling tool with Claude AI integration.

## Features

- 🤖 **AI-Powered**: Claude API integration for intelligent search and filtering
- 🔍 **Job Scraping**: Search multiple job platforms with a single query
- 🕸️ **General Crawler**: Find products, prices, or any information with natural language queries  
- 🛡️ **Protection Layer**: VPN/proxy support with browser fingerprinting
- 🧠 **Smart Filtering**: Automatically removes bootcamps and low-quality listings
- 📊 **Multiple Formats**: HTML, JSON, and CSV output formats

## Architecture

The application follows a modular architecture with these key components:

1. **Configuration Manager**: Handles settings storage and retrieval
2. **Claude Service**: Provides 4 independent API call nodes for different AI functions  
3. **Protection Service**: Manages VPN/proxy connections with browser fingerprinting
4. **Scraper Engine**: Handles both job scraping and general web crawling
5. **GUI Interface**: User-friendly interface for all functionality

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gravy-scraper.git
cd gravy-scraper

# Install dependencies
pip install -r requirements.txt