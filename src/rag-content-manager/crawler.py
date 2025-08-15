import asyncio
import fnmatch
import json
import os
import re
import time
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse, urlencode
from playwright.async_api import async_playwright, Playwright, Page
# Re-import Playwright-specific error types to resolve NameError
from playwright._impl._errors import TargetClosedError, Error as PlaywrightError 

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

def _get_version_rank_and_numeric(
    url_str: str, 
    version_param_name: str, 
    preferred_list: list[str]
) -> tuple[float, float]:
    """
    Extracts version information from a URL for comparison.
    Returns a tuple (preference_rank, -numeric_version) where:
    - preference_rank: Lower number means higher preference (0 = most preferred).
                       float('inf') if not found in preferred_list.
    - -numeric_version: Negative numeric version for tie-breaking:
                        higher numeric version results in a smaller (more preferred) value
                        when comparing tuples.
    """
    parsed_url = urlparse(url_str)
    query_params = parse_qs(parsed_url.query)
    version_str_list = query_params.get(version_param_name, [])
    
    full_version_id = version_str_list[0] if version_str_list else None
    
    # 1. Determine preference rank based on explicit list
    rank = float('inf') # Default: very low preference if not in explicit list
    if full_version_id and preferred_list: # Ensure preferred_list is not empty
        try:
            rank = preferred_list.index(full_version_id) # Lower index = higher preference (e.g., 0 is best)
        except ValueError:
            # Not in preferred list, so rank remains float('inf')
            pass 

    # 2. Extract numeric version for tie-breaking within rank or for unlisted versions
    numeric_version = 0.0 # Default numeric version
    if full_version_id:
        # Regex to find numbers like "9.0", "10.0", "6.0" from strings like "net-maui-9.0"
        match = re.search(r'(\d+(\.\d+)?)', version_str_list[0]) # Use version_str_list[0] directly
        if match:
            try:
                numeric_version = float(match.group(1))
            except ValueError:
                pass # numeric_version remains 0.0 if float conversion fails

    # Return (rank, -numeric_version) for tuple comparison
    # Lower rank is better. For same rank, smaller -numeric_version (i.e., larger numeric_version) is better.
    return (rank, -numeric_version)


async def run_crawler(
    playwright: Playwright, 
    start_url: str, 
    globs: list[str], 
    max_concurrency: int = 20,
    url_normalization_rules: dict = None,
    max_urls_to_find: int = None
) -> list[dict]:
    """
    Crawls a given start URL, enqueues links based on globs, and returns found URLs with titles.
    Prioritizes newer versions of pages based on a 'view' query parameter if specified
    via `url_normalization_rules.version_preference_order`.
    Also collects image URLs found on each page.
    """
    # Set default normalization rules if not provided
    rules = {
        'strip_fragments': True,
        'sort_query_params': True,
        'ignored_query_parameters': [],
        'remove_trailing_slash_from_paths': False,
        'version_preference_order': [] # Default to empty list for preference handling
    }
    if url_normalization_rules:
        rules.update(url_normalization_rules)

    start_time = time.time()
    # found_pages_data now stores normalized_url as key, and a dict value containing:
    # 'normalized_url', 'original_url', 'title', and 'image_urls'
    found_pages_data = {} 
    to_crawl_queue = asyncio.Queue()
    
    # Create a copy of rules to pass to _normalize_url, excluding version_preference_order
    normalize_url_params = {k: v for k, v in rules.items() if k != 'version_preference_order'}

    # Initial setup: Put the start URL into the queue and mark its normalized version as visited.
    normalized_start_url = _normalize_url(start_url, **normalize_url_params)
    await to_crawl_queue.put(start_url)
    visited_or_queued_urls = {normalized_start_url}

    # Define common image extensions for filtering and collection
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp')

    # Lock for protecting access to found_pages_data and visited_or_queued_urls during concurrent updates
    # This is crucial for preventing race conditions with `found_pages_data` accuracy.
    data_access_lock = asyncio.Lock()

    print(f"       - Starting crawl for: {start_url} with {max_concurrency} concurrent workers.")
    if max_urls_to_find is not None:
        print(f"       - Stopping after {max_urls_to_find} unique URLs are found.")
    print(f"       - Normalization rules: {rules}")

    async def worker(worker_id: int):
        browser = None
        context = None
        page = None
        try:
            browser = await playwright.chromium.launch()
            context = await browser.new_context()
            page = await context.new_page()

            while True:
                try:
                    request_url = await asyncio.wait_for(to_crawl_queue.get(), timeout=0.5)
                except asyncio.TimeoutError:
                    break

                try:
                    # Check early exit after fetching from queue
                    async with data_access_lock:
                        if max_urls_to_find is not None and len(found_pages_data) >= max_urls_to_find:
                            to_crawl_queue.task_done()
                            continue

                    normalized_request_url = _normalize_url(request_url, **normalize_url_params)
                    should_process_and_store = True

                    # Check for duplicate/less preferred URLs
                    async with data_access_lock:
                        if normalized_request_url in found_pages_data:
                            stored_page_info = found_pages_data[normalized_request_url]
                            current_url_comparison_value = _get_version_rank_and_numeric(
                                request_url, 
                                "view", 
                                rules.get('version_preference_order', [])
                            )
                            stored_url_comparison_value = _get_version_rank_and_numeric(
                                stored_page_info['original_url'], 
                                "view", 
                                rules.get('version_preference_order', [])
                            )
                            if current_url_comparison_value < stored_url_comparison_value:
                                should_process_and_store = True
                            else:
                                should_process_and_store = False  # Skip, stored is preferred

                    if not should_process_and_store:
                        to_crawl_queue.task_done()
                        continue

                    try:
                        await page.goto(request_url, wait_until="networkidle")
                        page_title = await page.title()
                        img_srcs = await page.evaluate('Array.from(document.querySelectorAll("img[src]")).map(img => img.src)')
                        href_img_links = await page.evaluate('Array.from(document.querySelectorAll("a[href]")).map(a => a.href)')
                        media_links = set(img_srcs) | set(href_img_links)
                        page_image_urls = []
                        for link in media_links:
                            absolute_link = urljoin(request_url, link)
                            if urlparse(absolute_link).path.lower().endswith(IMAGE_EXTENSIONS):
                                page_image_urls.append(absolute_link)
                        page_image_urls = list(set(page_image_urls))  # Deduplicate

                        async with data_access_lock:
                            found_pages_data[normalized_request_url] = {
                                'normalized_url': normalized_request_url,
                                'original_url': request_url,
                                'title': page_title,
                                'image_urls': page_image_urls
                            }

                        # Discover new links and enqueue
                        hrefs = await page.evaluate('Array.from(document.querySelectorAll("a[href]")).map(a => a.href)')
                        for href in hrefs:
                            full_url = urljoin(request_url, href)
                            if urlparse(full_url).path.lower().endswith(IMAGE_EXTENSIONS):
                                continue
                            normalized_link = _normalize_url(full_url, **normalize_url_params)
                            matched = any(fnmatch.fnmatch(full_url, glob) for glob in globs)
                            async with data_access_lock:
                                # Only enqueue new URLs if we haven't reached max_urls_to_find
                                if (
                                    matched and
                                    normalized_link not in visited_or_queued_urls and
                                    (max_urls_to_find is None or len(found_pages_data) < max_urls_to_find)
                                ):
                                    await to_crawl_queue.put(full_url)
                                    visited_or_queued_urls.add(normalized_link)

                    except Exception as e:
                        print(f"Worker {worker_id}: error processing {request_url}: {e}")

                    finally:
                        to_crawl_queue.task_done()

                except Exception as e:
                    # If any error occurs after get(), mark task done and continue
                    print(f"Worker {worker_id}: unexpected error after fetching from queue: {e}")
                    to_crawl_queue.task_done()

        finally:
            if page: await page.close()
            if context: await context.close()
            if browser: await browser.close()



    # Create and start the worker tasks
    workers = [asyncio.create_task(worker(i)) for i in range(max_concurrency)]
    
    # Wait until all URLs in the queue have been processed by the workers.
    # This will naturally stop when the queue is empty AND all tasks put into it are marked done.
    await to_crawl_queue.join() 
    
    # Cancel any worker tasks that are still running (e.g., waiting for new items).
    # This is a cleanup step after the queue has been processed.
    for w in workers:
        #if not w.done():
        w.cancel()
    
    # Gather all worker tasks to ensure they finish their cleanup (e.g., browser closing)
    # and to retrieve any exceptions.
    results = await asyncio.gather(*workers, return_exceptions=True)

    # Iterate through results to "retrieve" any exceptions and prevent "Future exception was never retrieved" warnings.
    for result in results:
        if isinstance(result, (TargetClosedError, PlaywrightError, asyncio.CancelledError)):
            # These are expected errors/cancellations during controlled shutdown.
            pass # Suppress output as requested for development
        elif isinstance(result, Exception):
            # Log any other truly unexpected exceptions
            print(f"       - Unexpected exception in gathered task: {result}")

    end_time = time.time()
    total_crawl_duration = end_time - start_time
    minutes = int(total_crawl_duration // 60)
    seconds = total_crawl_duration % 60

    print(f"       - Crawl finished for {start_url}. Found {len(found_pages_data)} unique base links.")
    print(f"       - Total crawl time: {minutes} minutes {seconds:.2f} seconds.") 
    
    # Return the collected data as a list of dictionaries.
    # Apply max_urls_to_find limit to the *returned* pages if set.
    sorted_pages = sorted(found_pages_data.values(), key=lambda page: page['normalized_url'])
    if max_urls_to_find is not None:
        sorted_pages = sorted_pages[:max_urls_to_find]

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
