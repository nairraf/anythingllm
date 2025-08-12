import asyncio
import json
import os
import re
import time # Import the time module
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, Playwright, Page

async def run_crawler(playwright: Playwright, start_url: str, globs: list[str], max_concurrency: int = 20) -> list[dict]:
    """
    Crawls a given start URL, enqueues links based on globs, and returns found URLs with titles.
    Mimics the PlaywrightCrawler behavior using asyncio and Playwright.

    Args:
        playwright: The Playwright instance.
        start_url: The URL to start crawling from.
        globs: A list of glob patterns for URL filtering.
        max_concurrency: The maximum number of concurrent browser tabs/workers.
    """
    # Record the start time of the crawl
    start_time = time.time()

    # Dictionary to store unique URLs and their titles, keyed by the normalized URL (no fragment)
    # This ensures only one entry per page (fragment ignored)
    # Stores {normalized_url: {'url': original_url_crawled, 'title': title}}
    found_pages_data = {} 
    
    # Asynchronous queue to manage URLs waiting to be crawled
    to_crawl_queue = asyncio.Queue()
    await to_crawl_queue.put(start_url) # Add the starting URL to the queue
    
    # Set to keep track of *normalized* URLs that have been added to the queue or already processed.
    # This prevents redundant processing of the same page (regardless of fragment).
    visited_or_queued_urls = {urlparse(start_url)._replace(fragment="").geturl()}

    print(f"      - Starting crawl for: {start_url} with {max_concurrency} concurrent workers.")

    async def worker():
        """
        Worker function to process URLs from the queue using a Playwright browser instance.
        Each worker maintains its own browser context and page.
        """
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()

        try:
            while True:
                try:
                    # Get a URL from the queue without waiting if empty
                    request_url = to_crawl_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break # Exit loop if no more URLs in the queue

                # Normalize the current request_url by removing its fragment for deduplication logic
                parsed_request_url = urlparse(request_url)
                normalized_request_url = parsed_request_url._replace(fragment="").geturl()

                # Check if this normalized URL has already been fully processed and stored
                if normalized_request_url in found_pages_data:
                    to_crawl_queue.task_done()
                    continue # Skip if already processed this base URL

                try:
                    # Navigate to the URL and wait for the DOM to be loaded
                    await page.goto(request_url, wait_until="networkidle")
                    
                    # Extract the page title
                    page_title = await page.title()
                    
                    # Store the original URL and its title, keyed by the normalized URL
                    # This ensures only one entry per logical page
                    found_pages_data[normalized_request_url] = {
                        'url': request_url, 
                        'title': page_title
                    }
                    
                    #print(f"  Processing {request_url} - Title: {page_title}")

                    # Extract all 'href' attributes from anchor tags on the page
                    hrefs = await page.evaluate('''
                        Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
                    ''')

                    # Enqueue discovered links based on provided glob patterns
                    for href in hrefs:
                        full_url = urljoin(request_url, href) # Resolve relative URLs to absolute ones
                        
                        # Normalize the link found for deduplication check
                        parsed_full_url = urlparse(full_url)
                        normalized_link_for_deduplication = parsed_full_url._replace(fragment="").geturl()

                        matched = False
                        # Check if the full URL matches any of the glob patterns (globs are not fragment-aware)
                        for glob_pattern in globs:
                            # Convert glob pattern to a regex pattern for flexible matching
                            regex_pattern = re.compile(glob_pattern.replace('*', '.*').replace('?', '.?'))
                            if regex_pattern.match(full_url): # Match glob against original full_url
                                matched = True
                                break
                        
                        # If matched and the normalized URL has not been visited/queued, add to queue
                        if matched and normalized_link_for_deduplication not in visited_or_queued_urls:
                            await to_crawl_queue.put(full_url) # Put the original full URL into the queue
                            visited_or_queued_urls.add(normalized_link_for_deduplication) # Add normalized URL to visited set

                except Exception as e:
                    print(f"        Error processing {request_url}: {e}")
                finally:
                    # Mark the task as done in the queue, regardless of success or failure
                    to_crawl_queue.task_done()
        finally:
            # Ensure the browser context and browser are closed after the worker finishes
            await context.close()
            await browser.close()


    # Create and start the worker tasks
    workers = [asyncio.create_task(worker()) for _ in range(max_concurrency)]
    
    # Wait until all URLs in the queue have been processed by the workers
    await to_crawl_queue.join() 
    
    # Cancel any worker tasks that are still running (e.g., waiting for new items)
    for w in workers:
        w.cancel()
    
    # Gather all worker tasks to ensure they finish their cleanup (e.g., browser closing)
    # return_exceptions=True prevents asyncio.gather from stopping on the first cancelled task
    await asyncio.gather(*workers, return_exceptions=True)

    # Record the end time and calculate duration
    end_time = time.time()
    total_crawl_duration = end_time - start_time
    minutes = int(total_crawl_duration // 60)
    seconds = total_crawl_duration % 60

    print(f"      - Crawl finished for {start_url}. Found {len(found_pages_data)} unique base links.")
    print(f"      - Total crawl time: {minutes} minutes {seconds:.2f} seconds.") # Print the total crawl time
    
    # Return the collected data as a list of dictionaries
    # Sort the items by URL for consistent output order
    sorted_pages = sorted(found_pages_data.values(), key=lambda page: page['url'])
    return sorted_pages


# async def main():
#     """
#     Main function to read crawl job configurations from a JSON file
#     and execute the crawler for each job.
#     """
#     crawl_jobs = []
#     try:
#         # Read the links configuration file
#         with open(LINKS_FILE, 'r', encoding='utf-8') as f:
#             file_content = f.read()
#         crawl_jobs = json.loads(file_content)
#     except FileNotFoundError:
#         print(f"Error: Config file '{LINKS_FILE}' not found.")
#         exit(1) # Exit if the config file is missing
#     except json.JSONDecodeError as e:
#         print(f"Error parsing config file '{LINKS_FILE}': {e}")
#         exit(1) # Exit if the JSON is malformed
#     except Exception as e:
#         print(f"Error reading config file: {e}")
#         exit(1)

#     # Initialize Playwright asynchronously
#     async with async_playwright() as playwright:
#         # Iterate through each crawl job and run the crawler
#         for job in crawl_jobs:
#             # You can now add 'max_concurrency' to your job object in links.json,
#             # or pass a fixed value here, e.g., max_concurrency=10
#             pages_found = await run_crawler(
#                 playwright, 
#                 job['url'], 
#                 job['globs'],
#                 max_concurrency=job.get('concurrency', 20) # Use 'concurrency' from job or default to 20
#             )
            
#             #print(f"\n--- Pages found for {job['url']} ---")
#             #for page in pages_found:
#                 # You can now access page['url'] and page['title']
#             #    print(f"  URL: {page['url']}, Title: {page['title']}")
#             #print("-" * 30)


# if __name__ == "__main__":
#     # --- Setup for Demonstration ---
#     # Create a dummy links.json file if it doesn't exist
#     # This makes the script runnable out-of-the-box for testing
#     if not os.path.exists(LINKS_FILE):
#         dummy_config = [
#             {
#                 "url": "https://learn.microsoft.com/en-us/dotnet/communitytoolkit/maui/",
#                 "globs": ["https://learn.microsoft.com/en-us/dotnet/communitytoolkit/**"],
#                 "concurrency": 40,
#                 "category": "mslearn-maui-community",
#                 "workspaces": "selos-main, selos-development, selos-experiments",
#                 "tags": [
#                     "",
#                     ""
#                 ]
#             }
#         ]
#         with open(LINKS_FILE, 'w', encoding='utf-8') as f:
#             json.dump(dummy_config, f, indent=4) # Write with indentation for readability
#         print(f"Created a dummy '{LINKS_FILE}' for demonstration.")
#         print("You can modify it with your desired crawl jobs.")
#         print("-" * 30)

#     # Run the main asynchronous function
#     asyncio.run(main())
