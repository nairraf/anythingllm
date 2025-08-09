from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin, urlparse, urlunparse
import sys

def get_sublinks_selenium(url):
    """
    Uses Selenium to scrape a URL, waiting for JavaScript to render content.
    """
    options = Options()
    options.add_argument("--headless")  # Run the browser in headless mode
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        parsed_url = urlparse(url)
        path_segments = parsed_url.path.split('/')
        parent_path = '/'.join(path_segments[:-1])
        parent_url = urlunparse(parsed_url._replace(path=parent_path, query='', fragment=''))
        
        # Add a trailing slash to the path if necessary for consistency
        if parent_path and not parent_path.endswith('/'):
            parent_url += '/'

        print(f"Using {parent_url} as Parent Path")
        # You might need to add a wait here to give JavaScript time to load content
        # from selenium.webdriver.support.ui import WebDriverWait
        # from selenium.webdriver.support import expected_conditions as EC
        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_all_elements_located((By.TAG_NAME, "a"))
        # )

        sublinks = set()
        
        # Find all <a> tags after the page is fully rendered
        links = driver.find_elements(By.TAG_NAME, "a")
        
        for link in links:
            href = link.get_attribute('href')
            if href:
                # Same filtering logic as before
                if href.startswith(parent_url) or href.startswith('/'):
                    absolute_url = urljoin(parent_url, href)
                    sublinks.add(absolute_url)
        
        return sublinks

    except Exception as e:
        print(f"Error with Selenium: {e}")
        return set()
    finally:
        if 'driver' in locals():
            driver.quit() # Always close the browser instance

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scraper_selenium.py <parent_url>")
        sys.exit(1)
    
    parent_url = sys.argv[1]
    all_sublinks = get_sublinks_selenium(parent_url)

    if all_sublinks:
        print(f"Found {len(all_sublinks)} sublinks for {parent_url}:")
        for sublink in all_sublinks:
            print(sublink)
    else:
        print("No sublinks found.")