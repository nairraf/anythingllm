import asyncio
import json
import os
import re
import time # Import the time module
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse, urlencode
from playwright.async_api import async_playwright, Playwright, Page

def _normalize_url(
    url: str,
    strip_fragments: bool = True,
    sort_query_params: bool = True,
    ignored_query_parameters: list[str] = None,
    remove_trailing_slash_from_paths: bool = False
) -> str:
    """
    Normalizes a URL by stripping fragments, sorting/ignoring query parameters,
    and optionally removing trailing slashes from paths.

    Args:
        url: The URL string to normalize.
        strip_fragments: If True, removes the fragment (part after #).
        sort_query_params: If True, sorts query parameters alphabetically.
        ignored_query_parameters: A list of query parameter names to remove.
        remove_trailing_slash_from_paths: If True, removes trailing slash from path
                                          unless it's part of a file name.

    Returns:
        The normalized URL string.
    """
    parsed = urlparse(url)

    # 1. Strip fragment
    if strip_fragments:
        parsed = parsed._replace(fragment="")

    # 2. Process query parameters
    query_params_dict = parse_qs(parsed.query, keep_blank_values=True)
    if ignored_query_parameters:
        for param in ignored_query_parameters:
            query_params_dict.pop(param, None) # Remove if exists

    # Sort parameters and rebuild query string
    if sort_query_params:
        # urlencode expects a list of 2-item tuples for doseq=True
        sorted_items = sorted(query_params_dict.items())
        rebuilt_query = urlencode(sorted_items, doseq=True)
        parsed = parsed._replace(query=rebuilt_query)
    else:
        # If not sorting, just rebuild the query from potentially removed params
        parsed = parsed._replace(query=urlencode(query_params_dict, doseq=True))

    # 3. Handle trailing slashes
    if remove_trailing_slash_from_paths:
        path = parsed.path
        # Check if path ends with a slash AND doesn't seem to have a file extension
        # (e.g., /doc/ vs /doc/file.html)
        if path.endswith('/') and '.' not in os.path.basename(path):
            parsed = parsed._replace(path=path.rstrip('/'))

    return urlunparse(parsed)

async def run_crawler(
    playwright: Playwright, 
    start_url: str, 
    globs: list[str], 
    max_concurrency: int = 20,
    url_normalization_rules: dict = None,
    max_urls_to_find: int = None # New parameter for the limit
) -> list[dict]:
    """
    Crawls a given start URL, enqueues links based on globs, and returns found URLs with titles.
    Mimics the PlaywrightCrawler behavior using asyncio and Playwright.

    Args:
        playwright: The Playwright instance.
        start_url: The URL to start crawling from.
        globs: A list of glob patterns for URL filtering.
        max_concurrency: The maximum number of concurrent browser tabs/workers.
        url_normalization_rules: A dictionary of rules for URL normalization.
                                 Keys: 'strip_fragments', 'sort_query_params',
                                 'ignored_query_parameters', 'remove_trailing_slash_from_paths'.
        max_urls_to_find: An optional integer. If set, the crawler will stop
                          after finding this many unique URLs.
    """
    # Set default normalization rules if not provided
    rules = {
        'strip_fragments': True,
        'sort_query_params': True, # Default to sorting for better consistency
        'ignored_query_parameters': [],
        'remove_trailing_slash_from_paths': False # Default to False, can be dangerous
    }
    if url_normalization_rules:
        rules.update(url_normalization_rules)

    # Record the start time of the crawl
    start_time = time.time()

    # Dictionary to store unique pages and their data, keyed by the normalized URL
    # Stores {normalized_url: {'normalized_url': normalized_url, 'original_url': original_url, 'title': title}}
    found_pages_data = {} 
    
    # Asynchronous queue to manage URLs waiting to be crawled
    to_crawl_queue = asyncio.Queue()
    
    # Normalize the start URL before adding to queue and visited set
    normalized_start_url = _normalize_url(start_url, **rules)
    await to_crawl_queue.put(start_url) # Always put the original URL into the queue to navigate to
    
    # Set to keep track of *normalized* URLs that have been added to the queue or already processed.
    visited_or_queued_urls = {normalized_start_url}

    print(f"       - Starting crawl for: {start_url} with {max_concurrency} concurrent workers.")
    if max_urls_to_find is not None:
        print(f"       - Stopping after {max_urls_to_find} unique URLs are found.")
    print(f"       - Normalization rules: {rules}")

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
                # Check if we've reached the limit
                if max_urls_to_find is not None and len(found_pages_data) >= max_urls_to_find:
                    # Signal that we're done by clearing the queue and breaking
                    while not to_crawl_queue.empty():
                        to_crawl_queue.get_nowait() # Consume items
                        to_crawl_queue.task_done() # Mark as done
                    break # Exit worker loop

                try:
                    # Get a URL from the queue without waiting if empty
                    request_url = to_crawl_queue.get_nowait()
                except asyncio.QueueEmpty:
                    # If queue is empty, we might be done or waiting for other workers
                    # We'll break here, and the main `to_crawl_queue.join()` will ensure all
                    # active tasks complete before the crawl truly ends.
                    break 

                # Normalize the current request_url for deduplication logic *before* processing
                normalized_request_url = _normalize_url(request_url, **rules)

                # Check if this normalized URL has already been fully processed and stored
                if normalized_request_url in found_pages_data:
                    to_crawl_queue.task_done()
                    continue # Skip if already processed this base URL

                try:
                    # Navigate to the URL
                    await page.goto(request_url, wait_until="networkidle")
                    
                    # Extract the page title
                    page_title = await page.title()
                    
                    # Check the limit again before adding, in case another worker just filled it
                    if max_urls_to_find is not None and len(found_pages_data) >= max_urls_to_find:
                        to_crawl_queue.task_done()
                        break # Exit worker if limit reached during page processing

                    # Store the *normalized* URL and its title, keyed by the normalized URL.
                    # This ensures only one entry per logical page and the 'url' field is normalized.
                    found_pages_data[normalized_request_url] = {
                        'normalized_url': normalized_request_url, # Store the normalized URL here
                        'original_url': request_url,              # Store the original URL here
                        'title': page_title
                    }
                    
                    #print(f"   Processing {request_url} - Title: {page_title}")

                    # Extract all 'href' attributes from anchor tags on the page
                    hrefs = await page.evaluate('''
                        Array.from(document.querySelectorAll('a[href]')).map(a => a.href)
                    ''')

                    # Enqueue discovered links based on provided glob patterns
                    for href in hrefs:
                        full_url = urljoin(request_url, href) # Resolve relative URLs to absolute ones
                        
                        # Normalize the link found for deduplication check *before* enqueuing
                        normalized_link_for_deduplication = _normalize_url(full_url, **rules)

                        matched = False
                        # Check if the original full URL matches any of the glob patterns
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
                    print(f"       - Error processing {request_url}: {e}")
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
    # Or, until the max_urls_to_find limit is hit and the queue is drained by workers
    await to_crawl_queue.join() 
    
    # Cancel any worker tasks that are still running (e.g., waiting for new items)
    for w in workers:
        w.cancel()
    
    # Gather all worker tasks to ensure they finish their cleanup (e.g., browser closing)
    await asyncio.gather(*workers, return_exceptions=True)

    # Record the end time and calculate duration
    end_time = time.time()
    total_crawl_duration = end_time - start_time
    minutes = int(total_crawl_duration // 60)
    seconds = total_crawl_duration % 60

    print(f"       - Crawl finished for {start_url}. Found {len(found_pages_data)} unique base links.")
    print(f"       - Total crawl time: {minutes} minutes {seconds:.2f} seconds.") # Print the total crawl time
    
    # Return the collected data as a list of dictionaries
    # Sort the items by URL for consistent output order (using normalized_url for sorting)
    sorted_pages = sorted(found_pages_data.values(), key=lambda page: page['normalized_url'])
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
#                 Print(f"  Normalized URL: {page['normalized_url']}")
#                 print(f"  Original URL:   {page['original_url']}")
#                 print(f"  Title:          {page['title']}")
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
