import asyncio
import json
import sqlite3
import textwrap
from db import DatabaseManager
from urllib.parse import urlparse
from get_web_markdown import scrape_to_markdown
import anythingllm_api
import crawler
import sys
import argparse
from playwright.async_api import async_playwright, Playwright, Page

# where the SQLite database resides
DB_File = r'..\..\db\sites.db'

# Define the path to the json job links configuration file
JOBS_FILE = './crawler_jobs.json'



# # db.insert_site(
# #     "https://learn.microsoft.com",
# #     'div[data-main-column]',
# #     'div.content',
# #     "Microsoft Learn"
# # )
# #
# #db.commit()


# db.set_site_config('learn.microsoft.com')



# # print (f"scraping completed, updating database")
# # db.insert_page(
# #     url=url,
# #     content=markdown,
# #     status="test"
# # )
# #db.commit()




# ### two workflows needed:
# ### 1: crawl through a URL structure and retrieve all appropriate URL's
# #      - add URL's to the pages table with a status of "new", with appropriate title, category, tags and workspaces
# #
# ### 2: another loop that simply looks for all 'new' pages:
# #      - extracts the relevant HTML for that URL and converts to markdown
# #      - stores the markdown in the pages row for that URL
# #      - uploads the document to anythingllm in the folder for it's category, and embeds it in the workspaces
# #      - marks that page as "complete" in the pages table
# ### workflow 1


# quit()


# ### workflow 2
# new_pages = db.get_pages()
# for page in new_pages:
#     print(f"""
#         Updating the following page to complete:
        
#         page_id: {page['page_id']}
#         url: {page['url']}
#         status: {page['status']}
#     """)
#     api_url = urlparse(page['url'])
#     basename = api_url.netloc
    
#     print (f"scraping '{page['url']}'")
#     markdown = scrape_to_markdown(
#         page['url'], 
#         db.site_parent_element, 
#         db.site_child_element, 
#         db.site_base_url,
#         page['category'],
#         page['tags']
#     )

#     db.update_page(
#         page_id=page['page_id'],
#         content=markdown,
#     )
    
#     try:
#         anythingllm_api.upload_to_anythingllm(
#             workspace_slug=page['workspaces'],
#             content=page['content'],
#             anythingllm_folder=f"{page['category']}",
#             anythingllm_filename=f"{page['category']}-{page['title']}"
#         )
#         db.update_page_status(page['page_id'])
#     except:
#         print("that failed")



# # anythingllm_api.upload_to_anythingllm(
# #     workspace_slug=anythingllm_workspace,
# #     file=filename,
# #     file_bytes=file_bytes,
# #     tags=[tag, "source:local"],
# #     anythingllm_folder=f"git-{anythingllm_workspace}",
# #     anythingllm_filename=llm_filename
# # )



# db.close()
#def print_help():
def get_links_json() -> list[dict]:
    """
    retrieves the list of jobs from the crawler_jobs.json file
    """
    crawl_jobs = []
    try:
        # Read the links configuration file
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()
        crawl_jobs = json.loads(file_content)
        return crawl_jobs
    except FileNotFoundError:
        print(f"Error: Config file '{JOBS_FILE}' not found.")
        exit(1) # Exit if the config file is missing
    except json.JSONDecodeError as e:
        print(f"Error parsing config file '{JOBS_FILE}': {e}")
        exit(1) # Exit if the JSON is malformed
    except Exception as e:
        print(f"Error reading config file: {e}")
        exit(1)

async def crawl_site(db: DatabaseManager, job: dict) -> None:
    """
    Performs a crawl for a specific site job

    crawls the site, finds all the links for that specific job, and updates the database with discovered URL's
    """
    print(f"    - performing crawl for job: {job['job']}")

    try:
        # get the current site config that we should use for this base url
        api_url = urlparse(job['url'])
        db.set_site_config(api_url.netloc)
    except Exception as e:
        print(f"Error setting Site config: {e}")

    async with async_playwright() as playwright:
        pages_found = await crawler.run_crawler(
            playwright, 
            job['url'], 
            job['globs'],
            max_concurrency=job.get('concurrency', 20) # Use 'concurrency' from job or default to 20
        )

        print(f"      - inserting {len(pages_found)} url's in db for job: {job['job']}")
        try:
            # insert the pages
            for page in pages_found:
                db.insert_new_page(
                    url=page['url'], 
                    title=page['title'],
                    job=job['job'],
                    tags=job['tags'],
                    workspaces=job['workspaces']
                )
        except Exception as e:
            print(f"Error Encountered: {e}")

async def crawler_mode(args: argparse.ArgumentParser, db: DatabaseManager) -> None:
    print("\ncrawler mode\n")

    job_list = get_links_json()

    run_specific_job = False
    if len(args.jobs) > 0:
        print("will perform specific job runs:")
        run_specific_job = True
        for argjob in args.jobs:
            for j in job_list:
                if "job" in j and j["job"] == argjob:
                    print(f" - Now processing job: {argjob}")
                    await crawl_site(db, j)
                    break
    
    # only perform the full job list if there were no jobs specified
    if run_specific_job == False:
        print("will perform a full job run")
        for job in job_list:
            await crawl_site(db, job)
    
    print(f"      - committing all changes in the DB")
    db.commit()


if __name__ == "__main__":
    # get the passed command line parameters
    parser = argparse.ArgumentParser(
        description="main rag data controller script to manage SQLite and AnythingLLM data.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--crawler",
        action="store_true",
        help="Enables crawler mode"
    )

    parser.add_argument(
        "--jobs",
        type=lambda s: [item.strip() for item in s.split(',')], # Custom type to split by comma and strip whitespace
        default=[], # Default to an empty list if no jobs are provided
        help=
    """    A comma-separated list of crawler job names to process.
    if ommitted, all defined jobs will be processed

    NOTE: requires --crawler
    
    Examples:
        --jobs cleanup,report,sync # no whitespaces
        --jobs "job1, job2, job3"  # allows whitespace seperation
    """
    )


    args = parser.parse_args()

    db = DatabaseManager(DB_File)

    # parse through the args
    if args.crawler:
        asyncio.run(crawler_mode(args, db))


    db.close()