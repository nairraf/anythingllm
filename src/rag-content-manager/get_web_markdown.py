#import trafilatura
import textwrap
import html2text
import os
import re
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

def make_links_absolute(markdown_content, base_url):
    """
    Finds all Markdown links and converts relative URLs to absolute URLs.
    """
    
    # Regex to find Markdown links like [text](url)
    link_regex = re.compile(r'\[.*?\]\((.*?)\)')
    
    def replace_link(match):
        url = match.group(1)
        # Check if the URL is relative
        if not urlparse(url).netloc:
            # Join with the base URL to make it absolute
            absolute_url = urljoin(base_url, url)
            return f"[{match.group(0)[1:-len(url)-1]}]({absolute_url})"
        return match.group(0)

    return link_regex.sub(replace_link, markdown_content)



def scrape_to_markdown(url, parent_selector, content_selector, base_url, tags=[], job="mslearn"):
    """
    Navigates to a URL, finds a parent container, then looks for all child elements
    matching content_selector, concatenates their HTML, converts it to markdown.
    """
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, wait_until='domcontentloaded')
            title = page.title()

            parent_element = page.locator(parent_selector).first
            if not parent_element:
                print(f"Parent selector '{parent_selector}' not found.")
                browser.close()
                return None

            # List to hold HTML content from all relevant divs
            all_html_parts = []
            
            # Find all child elements that match the content_selector
            content_divs = parent_element.locator(content_selector).all()

            # Loop through the found elements and collect their HTML content
            for div in content_divs:
                if div.inner_text().strip(): # Only include if it has actual text content
                    all_html_parts.append(div.inner_html())
            
            # If no specific content divs found or they were all empty, fall back to parent's html
            if not all_html_parts:
                print(f"No non-empty child content found with '{content_selector}'. Falling back to parent selector '{parent_selector}'.")
                html_content = parent_element.inner_html()
            else:
                # Concatenate all collected HTML parts
                html_content = "".join(all_html_parts)

            if not html_content:
                print("Could not find any content to scrape.")
                browser.close()
                return None

            h = html2text.HTML2Text()
            h.body_width = 0
            # Ensure links within the combined HTML are made absolute
            markdown_content = make_links_absolute(h.handle(html_content), base_url)

            metadata = f"""
                ---
                title: {title}
                source_url: {url}
                tags: {tags}
                crawler_job: {job}
                ---
            """
            # Use textwrap.dedent for clean multi-line YAML metadata
            markdown_content = f"{textwrap.dedent(metadata)}\n\n{markdown_content}"

            browser.close()
            return markdown_content
    except Exception as e:
        print(f"An error occurred during scraping {url}: {e}")
        return None

# --- Quick Test ---
# Make sure to create a 'cache_output' folder in your project directory
# before running this script.
#output_folder = "cache_output"
#if not os.path.exists(output_folder):
#    os.makedirs(output_folder)

# Example usage for the .NET API documentation page
#api_url = "https://learn.microsoft.com/en-us/dotnet/api/system.windows.forms.visualstyles.visualstyleelement.toolbar.splitbuttondropdown.hotchecked?view=windowsdesktop-9.0"
#api_url = "https://learn.microsoft.com/en-us/dotnet/maui/?view=net-maui-9.0"
#parent_selector = 'div[data-main-column]'
#content_selector = 'div.content'

#scrape_to_markdown(api_url, parent_selector, content_selector, output_folder, "https://learn.microsoft.com")

# Create a clean filename and path
# filename = url.strip('https://').replace('/','_').replace('?','').replace('=','') + '.md'
# file_path = os.path.join(output_path, filename)