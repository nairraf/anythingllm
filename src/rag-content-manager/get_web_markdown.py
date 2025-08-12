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



def scrape_to_markdown(url, parent_selector, content_selector, base_url, tags=[], category="mslearn"):
    """
    Navigates to a URL, finds a parent container, then looks for a non-empty
    child element to extract its content, convert it to markdown, and save it.
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
                return

            html_content = None
            # Find all child elements that match the content_selector
            content_divs = parent_element.locator(content_selector).all()

            # Loop through the found elements to find the one with actual content
            for div in content_divs:
                if div.inner_text().strip():
                    html_content = div.inner_html()
                    break # Stop looping once we find the correct content

            if not html_content:
                print(f"No non-empty child content found. Falling back to parent selector '{parent_selector}'.")
                html_content = parent_element.inner_html()

            if not html_content:
                print("Could not find any content.")
                browser.close()
                return

            h = html2text.HTML2Text()
            h.body_width = 0
            markdown_content = make_links_absolute(h.handle(html_content),base_url)
            metadata = f"""
                ---
                title: {title}
                source_url: {url}
                tags: {tags}
                category: {category}
                ---
            """
            markdown_content = f"{textwrap.dedent(metadata)}\n\n{markdown_content}"

            # (The code for making links absolute goes here, unchanged)
            #filename = url.strip('https://').replace('/','_').replace('?','').replace('=','') + '.md'
            #file_path = os.path.join(output_base_path, filename)
            #with open(file_path, 'w', encoding='utf-8') as f:
            #    f.write(f'# Content from: {url}\n\n')
            #    f.write(markdown_content)
            #print(f"Content saved to {file_path}")

            browser.close()
            return markdown_content
    except Exception as e:
        print(f"An error occurred: {e}")

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