"""
Locust load testing for URL Shortener Service

Separate user classes for each endpoint:
- CreateShortURLUser - Tests POST /shorten (create short URLs)
- RedirectUser - Tests GET /{short_code} (redirect to URLs)
- StatsUser - Tests GET /stats/{short_code} (get analytics)

Each user class has ONLY ONE task, so you can select which user class to run.

For RedirectUser and StatsUser, you can provide short codes via environment variable:
- LOCUST_SHORT_CODES: comma-separated list of short codes (e.g., "abc123,def456,ghi789")

Usage (command line):
    # Test only create endpoint
    locust -f locustfile.py CreateShortURLUser --host=http://localhost

    # Test only redirect endpoint
    locust -f locustfile.py RedirectUser --host=http://localhost

    # Test only stats endpoint
    locust -f locustfile.py StatsUser --host=http://localhost

Usage in UI:
    - Select which user class to run in the Locust web UI
    - Or specify user class via command line when starting Locust
"""

from locust import HttpUser, task, between, events
import os
import random


class CreateShortURLUser(HttpUser):
    """
    Tests ONLY the POST /shorten endpoint.
    Creates short URLs with very simple URLs.
    Select this user class to test URL creation only.
    """
    
    host = "http://nginx"  # Fixed host - do not change
    wait_time = between(1, 3)
    weight = 1  # Weight for user class selection
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Very simple URLs for testing
        self.simple_urls = [
            "https://example.com",
            "https://test.com",
            "https://demo.com",
            "https://sample.com",
            "https://example.org",
        ]
    
    @task(1)
    def create_short_url(self):
        """ONLY task: Create a short URL with a simple URL."""
        # Use very simple URLs
        original_url = random.choice(self.simple_urls)
        
        self.client.post(
            "/shorten",
            json={"original_url": original_url},
            headers={"Content-Type": "application/json"},
            name="Create Short URL"
        )


class RedirectUser(HttpUser):
    """
    Tests ONLY the GET /{short_code} redirect endpoint.
    
    If LOCUST_SHORT_CODES environment variable is set (comma-separated),
    it will use those short codes. Otherwise, it will generate random ones.
    Select this user class to test redirects only.
    """
    
    host = "http://nginx"  # Fixed host - do not change
    wait_time = between(1, 3)
    weight = 1  # Weight for user class selection
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Get short codes from environment variable if provided
        short_codes_env = os.getenv("LOCUST_SHORT_CODES", "")
        if short_codes_env:
            self.short_codes = [code.strip() for code in short_codes_env.split(",") if code.strip()]
            print(f"Using provided short codes: {self.short_codes}")
        else:
            self.short_codes = []
            print("No short codes provided. Will generate random short codes (may return 404).")
    
    @task(1)
    def redirect_to_url(self):
        """ONLY task: Test redirect to URL."""
        if self.short_codes:
            # Use provided short codes
            short_code = random.choice(self.short_codes)
        else:
            # Generate random short code (will likely return 404, but tests the endpoint)
            import string
            short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        # Follow redirects=False to test redirect response without following
        self.client.get(
            f"/{short_code}",
            allow_redirects=False,
            name="Redirect to URL"
        )


class StatsUser(HttpUser):
    """
    Tests ONLY the GET /stats/{short_code} endpoint.
    
    If LOCUST_SHORT_CODES environment variable is set (comma-separated),
    it will use those short codes. Otherwise, it will generate random ones.
    Select this user class to test stats only.
    """
    
    host = "http://nginx"  # Fixed host - do not change
    wait_time = between(1, 3)
    weight = 1  # Weight for user class selection
    
    def on_start(self):
        """Called when a simulated user starts."""
        # Get short codes from environment variable if provided
        short_codes_env = os.getenv("LOCUST_SHORT_CODES", "")
        if short_codes_env:
            self.short_codes = [code.strip() for code in short_codes_env.split(",") if code.strip()]
            print(f"Using provided short codes: {self.short_codes}")
        else:
            self.short_codes = []
            print("No short codes provided. Will generate random short codes (may return 404).")
    
    @task(1)
    def get_url_stats(self):
        """ONLY task: Get statistics for a short URL."""
        if self.short_codes:
            # Use provided short codes
            short_code = random.choice(self.short_codes)
        else:
            # Generate random short code (will likely return 404, but tests the endpoint)
            import string
            short_code = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        self.client.get(
            f"/stats/{short_code}",
            name="Get URL Statistics"
        )


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("=" * 60)
    print("URL Shortener Load Test Started")
    print("=" * 60)
    print(f"Target host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("=" * 60)
    print("URL Shortener Load Test Completed")
    print("=" * 60)

