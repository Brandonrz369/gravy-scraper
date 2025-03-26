import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import webbrowser
import os
import logging
import json

class GravyScraperApp:
    def __init__(self, config_manager, claude_service, protection_service, scraper_engine):
        self.config_manager = config_manager
        self.claude_service = claude_service
        self.protection_service = protection_service
        self.scraper_engine = scraper_engine
        self.logger = logging.getLogger("GravyScraperApp")
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Gravy Scraper")
        self.root.geometry("900x700")
        
        # Set up the UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the main UI elements"""
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.job_tab = ttk.Frame(self.notebook)
        self.general_tab = ttk.Frame(self.notebook)
        self.settings_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.job_tab, text="Job Scraper")
        self.notebook.add(self.general_tab, text="General Scraper")
        self.notebook.add(self.settings_tab, text="Settings")
        
        # Set up the content of each tab
        self.setup_job_tab()
        self.setup_general_tab()
        self.setup_settings_tab()
        
        # Create status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create license status indicator
        self.license_status_var = tk.StringVar()
        license_key = self.config_manager.get_value("license.key", "")
        if license_key:
            self.license_status_var.set(f"✓ Premium | {license_key}")
        else:
            self.license_status_var.set("Free Version")
        
        license_status = ttk.Label(self.root, textvariable=self.license_status_var, anchor=tk.E)
        license_status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_job_tab(self):
        """Set up the Job Scraper tab"""
        # Job search query frame
        query_frame = ttk.LabelFrame(self.job_tab, text="Custom Job Search Query")
        query_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(query_frame, text="Describe the job you're looking for in plain language:").pack(anchor=tk.W, padx=5, pady=5)
        
        self.job_query_text = tk.Text(query_frame, height=4, width=80)
        self.job_query_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Template selection
        template_frame = ttk.Frame(query_frame)
        template_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(template_frame, text="Or select a category:").pack(side=tk.LEFT)
        
        self.template_var = tk.StringVar()
        categories = [
            "Programming", 
            "Data Science", 
            "Marketing", 
            "Design", 
            "Customer Service",
            "Sales",
            "Finance",
            "Healthcare",
            "Education"
        ]
        template_combo = ttk.Combobox(template_frame, textvariable=self.template_var, values=categories, width=20)
        template_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(template_frame, text="Generate Template", command=self.generate_template).pack(side=tk.LEFT, padx=5)
        
        # Location frame
        location_frame = ttk.Frame(query_frame)
        location_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(location_frame, text="Location:").pack(side=tk.LEFT)
        
        self.location_var = tk.StringVar(value="Remote")
        location_entry = ttk.Entry(location_frame, textvariable=self.location_var, width=30)
        location_entry.pack(side=tk.LEFT, padx=5)
        
        # Job sources frame
        sources_frame = ttk.LabelFrame(self.job_tab, text="Options")
        sources_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Job sources checkboxes
        sources_label = ttk.Label(sources_frame, text="Job Sources:")
        sources_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.job_sources = {}
        sources = ["Indeed", "RemoteOK", "LinkedIn", "Freelancer", "Craigslist"]
        
        for i, source in enumerate(sources):
            var = tk.BooleanVar(value=self.config_manager.get_value(f"job_sources.{source}", True))
            self.job_sources[source] = var
            ttk.Checkbutton(sources_frame, text=source, variable=var).grid(row=0, column=i+1, padx=5, pady=5)
        
        # Background/test mode options
        options_frame = ttk.Frame(sources_frame)
        options_frame.grid(row=1, column=0, columnspan=6, sticky=tk.W, padx=5, pady=5)
        
        self.background_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Run in background (headless)", 
                        variable=self.background_var).pack(side=tk.LEFT, padx=5)
        
        self.test_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Test mode (no actual scraping)", 
                        variable=self.test_mode_var).pack(side=tk.LEFT, padx=5)
        
        # Protection status
        protection_frame = ttk.Frame(sources_frame)
        protection_frame.grid(row=2, column=0, columnspan=6, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(protection_frame, text="Protection:").pack(side=tk.LEFT, padx=5)
        
        protection_status = "Enabled" if self.protection_service.enabled else "Disabled"
        protection_service = self.protection_service.current_service
        
        protection_text = f"{protection_status} - Using {protection_service}"
        ttk.Label(protection_frame, text=protection_text).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.job_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Start Job Search", 
                  command=self.start_job_search).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="View Latest Jobs", 
                  command=self.view_latest_jobs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Save Configuration", 
                  command=self.save_job_config).pack(side=tk.LEFT, padx=5)
        
        # Output area
        output_frame = ttk.LabelFrame(self.job_tab, text="Output:")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.job_output_text = scrolledtext.ScrolledText(output_frame)
        self.job_output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_general_tab(self):
        """Set up the General Scraper tab"""
        # Query frame
        query_frame = ttk.LabelFrame(self.general_tab, text="Website Scraping Query")
        query_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(query_frame, text="What information are you looking for?").pack(anchor=tk.W, padx=5, pady=5)
        
        self.general_query_text = tk.Text(query_frame, height=4, width=80)
        self.general_query_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Examples
        examples_frame = ttk.Frame(query_frame)
        examples_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(examples_frame, text="Examples:").pack(side=tk.LEFT)
        
        examples = [
            "Find iPhone 12s below $200 on eBay",
            "Compare airline prices for NYC to LAX on April 15",
            "Find best baseball tickets prices for next week",
            "Look for apartments in Seattle under $2000"
        ]
        
        def set_example(example):
            self.general_query_text.delete(1.0, tk.END)
            self.general_query_text.insert(tk.END, example)
        
        for i, example in enumerate(examples):
            ttk.Button(examples_frame, text=f"Example {i+1}", 
                      command=lambda e=example: set_example(e)).pack(side=tk.LEFT, padx=5)
        
        # Website type selection
        type_frame = ttk.Frame(query_frame)
        type_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(type_frame, text="Type of websites to search:").pack(side=tk.LEFT)
        
        self.website_type_var = tk.StringVar(value="Any")
        website_type_combo = ttk.Combobox(type_frame, textvariable=self.website_type_var, width=30)
        website_type_combo['values'] = ("Any", "E-commerce", "News", "Travel", "Forums", "Social Media")
        website_type_combo.pack(side=tk.LEFT, padx=5)
        
        # Output format selection
        format_frame = ttk.Frame(query_frame)
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(format_frame, text="Output format:").pack(side=tk.LEFT)
        
        self.output_format_var = tk.StringVar(value="HTML")
        output_format_combo = ttk.Combobox(format_frame, textvariable=self.output_format_var, width=15)
        output_format_combo['values'] = ("HTML", "JSON", "CSV")
        output_format_combo.pack(side=tk.LEFT, padx=5)
        
        # Scraping options
        options_frame = ttk.LabelFrame(self.general_tab, text="Scraping Options")
        options_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Max pages option
        max_pages_frame = ttk.Frame(options_frame)
        max_pages_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(max_pages_frame, text="Maximum pages per site:").pack(side=tk.LEFT)
        
        self.max_pages_var = tk.IntVar(value=10)
        max_pages_spinbox = ttk.Spinbox(max_pages_frame, from_=1, to=100, textvariable=self.max_pages_var, width=5)
        max_pages_spinbox.pack(side=tk.LEFT, padx=5)
        
        # Protection status
        protection_frame = ttk.Frame(options_frame)
        protection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(protection_frame, text="Protection:").pack(side=tk.LEFT, padx=5)
        
        protection_status = "Enabled" if self.protection_service.enabled else "Disabled"
        protection_service = self.protection_service.current_service
        
        protection_text = f"{protection_status} - Using {protection_service}"
        ttk.Label(protection_frame, text=protection_text).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        button_frame = ttk.Frame(self.general_tab)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="Start Scraping", 
                  command=self.start_general_scraping).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="View Latest Results", 
                  command=self.view_latest_results).pack(side=tk.LEFT, padx=5)
        
        # Output area
        output_frame = ttk.LabelFrame(self.general_tab, text="Output:")
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.general_output_text = scrolledtext.ScrolledText(output_frame)
        self.general_output_text.pack(fill=tk.BOTH, expand=True)
    
    def setup_settings_tab(self):
        """Set up the Settings tab"""
        # License management frame
        license_frame = ttk.LabelFrame(self.settings_tab, text="License Management")
        license_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # License key field
        key_frame = ttk.Frame(license_frame)
        key_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(key_frame, text="License Key:").pack(side=tk.LEFT)
        
        self.license_key_var = tk.StringVar(value=self.config_manager.get_value("license.key", ""))
        license_key_entry = ttk.Entry(key_frame, textvariable=self.license_key_var, width=40)
        license_key_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(key_frame, text="Activate License", 
                  command=self.activate_license).pack(side=tk.LEFT, padx=5)
        
        # License status
        status_frame = ttk.Frame(license_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        
        license_status = self.config_manager.get_value("license.key", "") != ""
        status_text = "Valid" if license_status else "Invalid"
        valid_until = self.config_manager.get_value("license.valid_until", "")
        
        self.license_status_label = ttk.Label(
            status_frame, 
            text=f"{status_text}  Valid until: {valid_until}" if license_status else "Invalid"
        )
        self.license_status_label.pack(side=tk.LEFT, padx=5)
        
        # Enabled features
        features_frame = ttk.Frame(license_frame)
        features_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(features_frame, text="Enabled Features:").pack(side=tk.LEFT)
        
        features = self.config_manager.get_value("license.enabled_features", [])
        features_text = ", ".join(features) if features else "None"
        
        ttk.Label(features_frame, text=features_text).pack(side=tk.LEFT, padx=5)
        
        # Claude API configuration frame
        claude_frame = ttk.LabelFrame(self.settings_tab, text="Claude API Configuration")
        claude_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # API key field
        api_frame = ttk.Frame(claude_frame)
        api_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(api_frame, text="API Key:").pack(side=tk.LEFT)
        
        self.claude_api_key_var = tk.StringVar(value=self.config_manager.get_value("claude_api.api_key", ""))
        claude_api_key_entry = ttk.Entry(api_frame, textvariable=self.claude_api_key_var, width=40, show="*")
        claude_api_key_entry.pack(side=tk.LEFT, padx=5)
        
        # Model selection
        model_frame = ttk.Frame(claude_frame)
        model_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT)
        
        self.claude_model_var = tk.StringVar(value=self.config_manager.get_value("claude_api.model", "claude-3-opus-20240229"))
        claude_model_combo = ttk.Combobox(model_frame, textvariable=self.claude_model_var, width=30)
        claude_model_combo['values'] = ("claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307")
        claude_model_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(model_frame, text="Configure API", 
                  command=self.configure_claude_api).pack(side=tk.LEFT, padx=5)
        
        # Test API connection
        test_frame = ttk.Frame(claude_frame)
        test_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(test_frame, text="Test API Connection", 
                  command=self.test_claude_api).pack(side=tk.LEFT, padx=5)
        
        # VPN & Proxy configuration frame
        vpn_frame = ttk.LabelFrame(self.settings_tab, text="VPN & Proxy Configuration")
        vpn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Enable/disable protection
        enable_frame = ttk.Frame(vpn_frame)
        enable_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(enable_frame, text="Protection:").pack(side=tk.LEFT)
        
        self.protection_enabled_var = tk.BooleanVar(value=self.protection_service.enabled)
        ttk.Checkbutton(enable_frame, text="Enable Protection", 
                        variable=self.protection_enabled_var, 
                        command=self.toggle_protection).pack(side=tk.LEFT, padx=5)
        
        # Fingerprinting option
        fingerprint_frame = ttk.Frame(vpn_frame)
        fingerprint_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(fingerprint_frame, text="Browser Fingerprinting:").pack(side=tk.LEFT)
        
        self.fingerprinting_var = tk.BooleanVar(value=self.protection_service.fingerprinting)
        ttk.Checkbutton(fingerprint_frame, text="Enable", 
                        variable=self.fingerprinting_var, 
                        command=self.toggle_fingerprinting).pack(side=tk.LEFT, padx=5)
        
        # Proxy service selection
        service_frame = ttk.Frame(vpn_frame)
        service_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(service_frame, text="Configure Proxy Service:").pack(side=tk.LEFT)
        
        self.proxy_service_var = tk.StringVar(value=self.protection_service.current_service)
        proxy_service_combo = ttk.Combobox(service_frame, textvariable=self.proxy_service_var, width=20)
        proxy_service_combo['values'] = ("Direct", "BrightData", "ScraperAPI")
        proxy_service_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(service_frame, text="Setup Proxy", 
                  command=self.setup_proxy).pack(side=tk.LEFT, padx=5)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.settings_tab)
        buttons_frame.pack(fill=tk.X, padx=10, pady=20)
        
        ttk.Button(buttons_frame, text="Test Features", 
                  command=self.test_features).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="View Logs", 
                  command=self.view_logs).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="About", 
                  command=self.show_about).pack(side=tk.LEFT, padx=5)
        
        # Save all settings
        ttk.Button(buttons_frame, text="Save All Settings", 
                  command=self.save_all_settings).pack(side=tk.RIGHT, padx=5)
    
    def generate_template(self):
        """Generate a custom search template based on selected category"""
        category = self.template_var.get()
        if not category:
            return
        
        # Update status
        self.status_var.set(f"Generating template for {category}...")
        
        # Use threading to keep UI responsive
        def template_thread():
            try:
                # Generate template using Claude
                template = self.claude_service.generate_search_template(category)
                
                # Update job query text
                self.job_query_text.delete(1.0, tk.END)
                self.job_query_text.insert(tk.END, template)
                
                # Update status
                self.status_var.set("Template generated")
            
            except Exception as e:
                # Handle errors
                self.job_output_text.insert(tk.END, f"Error generating template: {e}\n")
                self.status_var.set("Error generating template")
        
        thread = threading.Thread(target=template_thread)
        thread.daemon = True
        thread.start()
    
    def start_job_search(self):
        """Start job search based on query"""
        # Get search parameters
        query = self.job_query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter a job search query")
            return
            
        location = self.location_var.get() if self.location_var.get() != "Remote" else None
        
        # Determine selected job sources
        sources = [source for source, var in self.job_sources.items() if var.get()]
        
        # Update status
        self.status_var.set("Searching for jobs...")
        self.job_output_text.delete(1.0, tk.END)
        self.job_output_text.insert(tk.END, f"Searching for: {query}\n")
        if location:
            self.job_output_text.insert(tk.END, f"Location: {location}\n")
        self.job_output_text.insert(tk.END, f"Sources: {', '.join(sources)}\n\n")
        
        # Use threading to keep UI responsive
        def search_thread():
            try:
                # Check if test mode is enabled
                if self.test_mode_var.get():
                    # Simulate search in test mode
                    import time
                    time.sleep(2)
                    self.job_output_text.insert(tk.END, "TEST MODE: No actual scraping performed\n")
                    self.job_output_text.insert(tk.END, "Would have searched for jobs matching the query\n")
                    self.status_var.set("Test search completed")
                    return
                
                # Perform real search
                jobs = self.scraper_engine.search_jobs(query, sources, location)
                
                # Update output
                if jobs:
                    self.job_output_text.insert(tk.END, f"Found {len(jobs)} matching jobs\n\n")
                    
                    # Display first 5 jobs
                    for i, job in enumerate(jobs[:5]):
                        self.job_output_text.insert(tk.END, f"{i+1}. {job.get('title', 'Unknown')}\n")
                        self.job_output_text.insert(tk.END, f"   Company: {job.get('company', 'Unknown')}\n")
                        self.job_output_text.insert(tk.END, f"   Location: {job.get('location', 'Unknown')}\n")
                        self.job_output_text.insert(tk.END, f"   Source: {job.get('source', 'Unknown')}\n\n")
                    
                    # Add view instructions
                    self.job_output_text.insert(tk.END, "Job report saved to gravy_jobs.html\n")
                    self.job_output_text.insert(tk.END, "Click 'View Latest Jobs' to open in browser\n")
                else:
                    self.job_output_text.insert(tk.END, "No matching jobs found\n")
                
                # Update status
                self.status_var.set("Job search completed")
            
            except Exception as e:
                # Handle errors
                self.job_output_text.insert(tk.END, f"Error: {e}\n")
                self.status_var.set("Error during job search")
                self.logger.error(f"Job search error: {e}")
        
        thread = threading.Thread(target=search_thread)
        thread.daemon = True
        thread.start()
    
    def view_latest_jobs(self):
        """Open job report in browser"""
        report_path = os.path.abspath("gravy_jobs.html")
        if os.path.exists(report_path):
            webbrowser.open(f"file://{report_path}")
        else:
            self.job_output_text.insert(tk.END, "No job report found. Run a search first.\n")
    
    def save_job_config(self):
        """Save job search configuration"""
        # Save job sources configuration
        for source, var in self.job_sources.items():
            self.config_manager.set_value(f"job_sources.{source}", var.get())
        
        messagebox.showinfo("Configuration Saved", "Job search configuration has been saved.")
    
    def start_general_scraping(self):
        """Start general scraping based on query"""
        # Get scraping parameters
        query = self.general_query_text.get(1.0, tk.END).strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter a scraping query")
            return
            
        max_pages = self.max_pages_var.get()
        
        # Update status
        self.status_var.set("Scraping websites...")
        self.general_output_text.delete(1.0, tk.END)
        self.general_output_text.insert(tk.END, f"Searching for: {query}\n")
        self.general_output_text.insert(tk.END, f"Maximum pages per site: {max_pages}\n\n")
        
        # Use threading to keep UI responsive
        def scrape_thread():
            try:
                # Perform scraping
                results = self.scraper_engine.crawl_general(query, max_pages)
                
                # Update output
                if results:
                    self.general_output_text.insert(tk.END, f"Found {len(results)} matching results\n\n")
                    
                    # Display first 5 results
                    for i, result in enumerate(results[:5]):
                        self.general_output_text.insert(tk.END, f"{i+1}. {result.get('title', 'Unknown')}\n")
                        if 'price' in result:
                            self.general_output_text.insert(tk.END, f"   Price: {result.get('price', '')}\n")
                        self.general_output_text.insert(tk.END, f"   Source: {result.get('source', 'Unknown')}\n\n")
                    
                    # Add view instructions
                    self.general_output_text.insert(tk.END, "Crawl results saved to gravy_crawler.html\n")
                    self.general_output_text.insert(tk.END, "Click 'View Latest Results' to open in browser\n")
                else:
                    self.general_output_text.insert(tk.END, "No matching results found\n")
                
                # Update status
                self.status_var.set("Web scraping completed")
            
            except Exception as e:
                # Handle errors
                self.general_output_text.insert(tk.END, f"Error: {e}\n")
                self.status_var.set("Error during web scraping")
                self.logger.error(f"General scraping error: {e}")
        
        thread = threading.Thread(target=scrape_thread)
        thread.daemon = True
        thread.start()
    
    def view_latest_results(self):
        """Open crawl report in browser"""
        report_path = os.path.abspath("gravy_crawler.html")
        if os.path.exists(report_path):
            webbrowser.open(f"file://{report_path}")
        else:
            self.general_output_text.insert(tk.END, "No crawl report found. Run a search first.\n")
    
    def activate_license(self):
        """Activate license with entered key"""
        license_key = self.license_key_var.get().strip()
        
        if not license_key:
            messagebox.showwarning("Input Required", "Please enter a license key")
            return
        
        # Validate license
        valid, license_info = self.config_manager.validate_license(license_key)
        
        if valid:
            # Update license status display
            valid_until = license_info.get("valid_until", "")
            features = license_info.get("enabled_features", [])
            
            self.license_status_label.config(text=f"Valid  Valid until: {valid_until}")
            self.license_status_var.set(f"✓ Premium | {license_key}")
            
            # Show success message
            messagebox.showinfo("License Activated", "License successfully activated!")
        else:
            # Show error message
            self.license_status_label.config(text="Invalid - License key not recognized")
            self.license_status_var.set("Free Version")
            messagebox.showerror("License Error", "Invalid license key!")
    
    def configure_claude_api(self):
        """Configure Claude API with entered key"""
        api_key = self.claude_api_key_var.get().strip()
        model = self.claude_model_var.get()
        
        if not api_key:
            messagebox.showwarning("Input Required", "API key is required")
            return
        
        # Update Claude service configuration
        self.claude_service.configure(api_key, model)
        
        # Show success message
        messagebox.showinfo("API Configured", "Claude API configuration saved!")
    
    def test_claude_api(self):
        """Test Claude API connection"""
        if not self.claude_service.api_key:
            messagebox.showwarning("API Key Required", "Please configure the Claude API first")
            return
        
        # Update status
        self.status_var.set("Testing Claude API connection...")
        
        # Use threading to keep UI responsive
        def test_thread():
            try:
                # Test the API with a simple request
                response = self.claude_service.get_completion("Hello, Claude! This is a test.")
                
                if response and not response.startswith("Error:"):
                    messagebox.showinfo("API Test", "Claude API connection successful!")
                else:
                    messagebox.showerror("API Test Failed", f"Claude API error: {response}")
                
                # Update status
                self.status_var.set("API test completed")
            
            except Exception as e:
                # Handle errors
                messagebox.showerror("API Test Failed", f"Error: {e}")
                self.status_var.set("API test failed")
        
        thread = threading.Thread(target=test_thread)
        thread.daemon = True
        thread.start()
    
    def toggle_protection(self):
        """Toggle protection on/off"""
        enabled = self.protection_enabled_var.get()
        self.protection_service.set_enabled(enabled)
        
        # Update status text in tabs
        protection_status = "Enabled" if enabled else "Disabled"
        protection_service = self.protection_service.current_service
        protection_text = f"{protection_status} - Using {protection_service}"
        
        self.status_var.set(f"Protection {protection_status}")
    
    def toggle_fingerprinting(self):
        """Toggle browser fingerprinting"""
        enabled = self.fingerprinting_var.get()
        self.protection_service.set_fingerprinting(enabled)
        self.status_var.set(f"Fingerprinting {('enabled' if enabled else 'disabled')}")
    
    def setup_proxy(self):
        """Configure selected proxy service"""
        service = self.proxy_service_var.get()
        
        if service == "Direct":
            # Set protection service to use direct connections
            self.protection_service.set_service("Direct")
            messagebox.showinfo("Proxy Configured", "Using direct connections (no proxy)")
            return
        
        # Open proxy configuration dialog based on selected service
        if service == "BrightData":
            self._show_brightdata_dialog()
        elif service == "ScraperAPI":
            self._show_scraperapi_dialog()
    
    def _show_brightdata_dialog(self):
        """Show dialog to configure BrightData proxy"""
        # Get existing configuration
        username = self.config_manager.get_value("protection.services.BrightData.username", "")
        password = self.config_manager.get_value("protection.services.BrightData.password", "")
        host = self.config_manager.get_value("protection.services.BrightData.host", "")
        port = self.config_manager.get_value("protection.services.BrightData.port", "")
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("BrightData Configuration")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Username field
        username_frame = ttk.Frame(dialog)
        username_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(username_frame, text="Username:").pack(side=tk.LEFT)
        
        username_var = tk.StringVar(value=username)
        username_entry = ttk.Entry(username_frame, textvariable=username_var, width=30)
        username_entry.pack(side=tk.LEFT, padx=5)
        
        # Password field
        password_frame = ttk.Frame(dialog)
        password_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(password_frame, text="Password:").pack(side=tk.LEFT)
        
        password_var = tk.StringVar(value=password)
        password_entry = ttk.Entry(password_frame, textvariable=password_var, width=30, show="*")
        password_entry.pack(side=tk.LEFT, padx=5)
        
        # Host field
        host_frame = ttk.Frame(dialog)
        host_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(host_frame, text="Host:").pack(side=tk.LEFT)
        
        host_var = tk.StringVar(value=host)
        host_entry = ttk.Entry(host_frame, textvariable=host_var, width=30)
        host_entry.pack(side=tk.LEFT, padx=5)
        
        # Port field
        port_frame = ttk.Frame(dialog)
        port_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT)
        
        port_var = tk.StringVar(value=port)
        port_entry = ttk.Entry(port_frame, textvariable=port_var, width=30)
        port_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_brightdata():
            # Save configuration
            self.protection_service.configure_brightdata(
                username_var.get(),
                password_var.get(),
                host_var.get(),
                port_var.get()
            )
            
            messagebox.showinfo("Proxy Configured", "BrightData proxy configuration saved!")
            dialog.destroy()
        
        ttk.Button(buttons_frame, text="Save", command=save_brightdata).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _show_scraperapi_dialog(self):
        """Show dialog to configure ScraperAPI proxy"""
        # Get existing configuration
        api_key = self.config_manager.get_value("protection.services.ScraperAPI.api_key", "")
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("ScraperAPI Configuration")
        dialog.geometry("400x100")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # API key field
        api_frame = ttk.Frame(dialog)
        api_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(api_frame, text="API Key:").pack(side=tk.LEFT)
        
        api_key_var = tk.StringVar(value=api_key)
        api_key_entry = ttk.Entry(api_frame, textvariable=api_key_var, width=30)
        api_key_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_scraperapi():
            # Save configuration
            self.protection_service.configure_scraperapi(api_key_var.get())
            
            messagebox.showinfo("Proxy Configured", "ScraperAPI configuration saved!")
            dialog.destroy()
        
        ttk.Button(buttons_frame, text="Save", command=save_scraperapi).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def test_features(self):
        """Test available features based on license"""
        # Get enabled features from license
        features = self.config_manager.get_value("license.enabled_features", [])
        
        # Create a dialog to display test results
        dialog = tk.Toplevel(self.root)
        dialog.title("Feature Test Results")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        
        # Create scrollable text area for results
        result_text = scrolledtext.ScrolledText(dialog)
        result_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Test each feature
        result_text.insert(tk.END, "Feature Test Results:\n\n")
        
        result_text.insert(tk.END, "1. Basic Scraping: ")
        if "basic_scraping" in features:
            result_text.insert(tk.END, "ENABLED ✓\n")
        else:
            result_text.insert(tk.END, "DISABLED ✗\n")
        
        result_text.insert(tk.END, "2. Commercial Proxies: ")
        if "commercial_proxies" in features:
            result_text.insert(tk.END, "ENABLED ✓\n")
        else:
            result_text.insert(tk.END, "DISABLED ✗\n")
        
        result_text.insert(tk.END, "3. Advanced Scraping: ")
        if "advanced_scraping" in features:
            result_text.insert(tk.END, "ENABLED ✓\n")
        else:
            result_text.insert(tk.END, "DISABLED ✗\n")
        
        result_text.insert(tk.END, "4. Claude Integration: ")
        if "claude_integration" in features:
            result_text.insert(tk.END, "ENABLED ✓\n")
        else:
            result_text.insert(tk.END, "DISABLED ✗\n")
        
        result_text.insert(tk.END, "5. General Scraping: ")
        if "general_scraping" in features:
            result_text.insert(tk.END, "ENABLED ✓\n")
        else:
            result_text.insert(tk.END, "DISABLED ✗\n")
        
        # Add Claude API test
        result_text.insert(tk.END, "\nClaude API Test: ")
        if self.claude_service.api_key:
            result_text.insert(tk.END, "API key configured\n")
            
            # Test API connection
            try:
                response = self.claude_service.get_completion("Hello, Claude! This is a test.")
                if not response.startswith("Error:"):
                    result_text.insert(tk.END, "API Connection: SUCCESS ✓\n")
                else:
                    result_text.insert(tk.END, f"API Connection: FAILED ✗ ({response})\n")
            except Exception as e:
                result_text.insert(tk.END, f"API Connection: FAILED ✗ ({str(e)})\n")
        else:
            result_text.insert(tk.END, "No API key configured\n")
        
        # Add Protection test
        result_text.insert(tk.END, "\nProtection Service Test: ")
        if self.protection_service.enabled:
            result_text.insert(tk.END, f"Using {self.protection_service.current_service}\n")
            
            # Test protection service
            try:
                html = self.protection_service.get_with_protection("https://httpbin.org/ip")
                if html:
                    result_text.insert(tk.END, "Connection Test: SUCCESS ✓\n")
                else:
                    result_text.insert(tk.END, "Connection Test: FAILED ✗\n")
            except Exception as e:
                result_text.insert(tk.END, f"Connection Test: FAILED ✗ ({str(e)})\n")
        else:
            result_text.insert(tk.END, "Protection disabled\n")
        
        # Add close button
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def view_logs(self):
        """View application logs"""
        # Check if log file exists
        if not os.path.exists("gravy_scraper.log"):
            messagebox.showinfo("No Logs", "No log file found.")
            return
        
        # Create a dialog to display logs
        dialog = tk.Toplevel(self.root)
        dialog.title("Application Logs")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        
        # Create scrollable text area for logs
        log_text = scrolledtext.ScrolledText(dialog)
        log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load and display log file
        try:
            with open("gravy_scraper.log", "r") as f:
                logs = f.read()
                log_text.insert(tk.END, logs)
                log_text.see(tk.END)  # Scroll to end
        except Exception as e:
            log_text.insert(tk.END, f"Error loading logs: {e}")
        
        # Add buttons
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def refresh_logs():
            log_text.delete(1.0, tk.END)
            try:
                with open("gravy_scraper.log", "r") as f:
                    logs = f.read()
                    log_text.insert(tk.END, logs)
                    log_text.see(tk.END)  # Scroll to end
            except Exception as e:
                log_text.insert(tk.END, f"Error loading logs: {e}")
        
        ttk.Button(buttons_frame, text="Refresh", command=refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """Gravy Scraper

Version: 1.0
© 2025 Gravy Solutions

A powerful scraping tool with Claude AI integration
for job search and general web crawling.

Features:
- Job scraping with AI-powered filtering and analysis
- General web crawling with intelligent query understanding
- VPN/proxy protection layer with browser fingerprinting
- Dynamic template generation for specialized searches
- Result filtering to remove low-quality listings
- HTML/JSON/CSV output formats
"""
        
        messagebox.showinfo("About Gravy Scraper", about_text)
    
    def save_all_settings(self):
        """Save all application settings"""
        # Save Claude API settings
        self.claude_service.configure(
            self.claude_api_key_var.get(),
            self.claude_model_var.get()
        )
        
        # Save protection settings
        self.protection_service.set_enabled(self.protection_enabled_var.get())
        self.protection_service.set_fingerprinting(self.fingerprinting_var.get())
        
        # Save job sources configuration
        for source, var in self.job_sources.items():
            self.config_manager.set_value(f"job_sources.{source}", var.get())
        
        messagebox.showinfo("Settings Saved", "All settings have been saved successfully.")
    
    def run(self):
        """Run the application"""
        self.root.mainloop()