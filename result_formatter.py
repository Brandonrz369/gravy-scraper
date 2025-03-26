# result_formatter.py - Format scraping results
import os
import json
import csv
import logging
from datetime import datetime

logger = logging.getLogger("ResultFormatter")

class ResultFormatter:
    """Class for formatting scraping results in different formats"""
    
    @staticmethod
    def format_job_results_as_html(jobs, query, filename="gravy_jobs.html"):
        """Generate HTML report for job listings"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Job Search Results - {query}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
                .job-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .job-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 5px; color: #2c3e50; }}
                .job-company {{ font-weight: bold; color: #3498db; }}
                .job-location {{ color: #7f8c8d; }}
                .job-salary {{ color: #27ae60; font-weight: bold; }}
                .job-source {{ display: inline-block; padding: 3px 8px; border-radius: 3px; 
                            font-size: 0.8em; background-color: #eee; margin: 5px 0; }}
                .job-description {{ margin-top: 10px; border-top: 1px solid #eee; padding-top: 10px; }}
                .job-link {{ display: inline-block; margin-top: 10px; padding: 5px 10px; background-color: #3498db; 
                           color: #fff; text-decoration: none; border-radius: 3px; }}
                .job-link:hover {{ background-color: #2980b9; }}
                .meta-info {{ text-align: right; font-size: 0.8em; color: #7f8c8d; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Job Search Results for: {query}</h1>
                <div class="meta-info">
                    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    <br>
                    Total jobs: {len(jobs)}
                </div>
        """
        
        for job in jobs:
            html += f"""
                <div class="job-card">
                    <div class="job-title">{job.get('title', 'Unknown')}</div>
                    <div class="job-company">{job.get('company', 'Unknown')}</div>
                    <div class="job-location">{job.get('location', 'Unknown')}</div>
            """
            
            # Add salary if available
            if job.get('salary') and job.get('salary') != "Not specified":
                html += f'<div class="job-salary">{job.get("salary")}</div>'
            
            html += f'<div class="job-source">{job.get("source", "Unknown")}</div>'
            
            # Add description if available
            if job.get('description'):
                html += f'<div class="job-description">{job.get("description")}</div>'
            
            # Add link if available
            if job.get('url'):
                html += f'<a href="{job.get("url")}" target="_blank" class="job-link">View Job</a>'
            
            html += """
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"Generated job report: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error generating job report: {e}")
            return False
    
    @staticmethod
    def format_crawl_results_as_html(results, query, filename="gravy_crawler.html"):
        """Generate HTML report for general crawl results"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Crawl Results - {query}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                h1 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
                .item-card {{ border: 1px solid #ddd; border-radius: 5px; padding: 15px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .item-title {{ font-size: 1.2em; font-weight: bold; margin-bottom: 5px; color: #2c3e50; }}
                .item-price {{ color: #27ae60; font-weight: bold; font-size: 1.1em; }}
                .item-source {{ display: inline-block; padding: 3px 8px; border-radius: 3px; 
                             font-size: 0.8em; background-color: #eee; margin: 5px 0; }}
                .item-link {{ display: inline-block; margin-top: 10px; padding: 5px 10px; background-color: #3498db; 
                            color: #fff; text-decoration: none; border-radius: 3px; }}
                .item-link:hover {{ background-color: #2980b9; }}
                .meta-info {{ text-align: right; font-size: 0.8em; color: #7f8c8d; margin-bottom: 20px; }}
                .item-property {{ margin: 3px 0; }}
                .property-name {{ font-weight: bold; color: #555; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Crawl Results for: {query}</h1>
                <div class="meta-info">
                    Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    <br>
                    Total results: {len(results)}
                </div>
        """
        
        for item in results:
            html += f"""
                <div class="item-card">
                    <div class="item-title">{item.get('title', 'Unknown')}</div>
            """
            
            # Add price if available
            if item.get('price'):
                html += f'<div class="item-price">{item.get("price")}</div>'
            
            html += f'<div class="item-source">{item.get("source", "Unknown")}</div>'
            
            # Add additional fields
            for key, value in item.items():
                if key not in ['title', 'price', 'url', 'source'] and value:
                    html += f'<div class="item-property"><span class="property-name">{key.capitalize()}:</span> {value}</div>'
            
            # Add link if available
            if item.get('url'):
                html += f'<a href="{item.get("url")}" target="_blank" class="item-link">View Item</a>'
            
            html += """
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.info(f"Generated crawl report: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error generating crawl report: {e}")
            return False
    
    @staticmethod
    def format_results_as_json(results, filename):
        """Format results as JSON file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Generated JSON file: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error generating JSON file: {e}")
            return False
    
    @staticmethod
    def format_results_as_csv(results, filename, fields=None):
        """Format results as CSV file"""
        if not results:
            logger.warning("No results to save to CSV")
            return False
        
        # If fields not specified, use keys from first result
        if not fields:
            fields = list(results[0].keys())
        
        try:
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(results)
            
            logger.info(f"Generated CSV file: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error generating CSV file: {e}")
            return False