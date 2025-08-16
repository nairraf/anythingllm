import asyncio
from datetime import datetime, timedelta
import json
import math
from pathlib import Path
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
DB_File = Path('../../db/sites.db')

# Define the path to the json job links configuration file
JOBS_FILE = './crawler_jobs.json'

#anythingllm junk/garbage folder name
junk_folder_name = "JUNK"

# -----------------------------------------------------------
# region functions
# -----------------------------------------------------------

# region GetJSON
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
# endregion GetJSON

# region Crawler
async def crawl_site(db: DatabaseManager, job: dict, max_pages: int = None, dbupdates: bool = True) -> None:
    """
    Performs a crawl for a specific site job

    crawls the site, finds all the links for that specific job, and updates the database with discovered URL's
    """
    print(f"    -  crawl job: {job['job']}")

    ## get the last runtime for the crawl to see if we run or skip
    jobs_last_update = db.get_jobs_runtime()
    cutoff = datetime.now() - timedelta(days=30)
    if not args.force:
        for j in jobs_last_update:
            if j['last_update'] and j['job']:
                if job['job'] == j['job']:
                    last_update_dt = datetime.strptime(j['last_update'], "%Y-%m-%d %H:%M:%S")
                    if last_update_dt > cutoff:
                        print(f"      - skipping run for job: {job['job']} - not time yet (>30 days)")
                        return
    
    print(f"      - running crawl for job: {job['job']}")

    if max_pages is not None and max_pages > 0:
        print(f"      MAXURLS of {max_pages} detected!")

    try:
        # get the current site config that we should use for this url
        db.set_site_config(job['url'])
    except Exception as e:
        print(f"Error setting Site config: {e}")

    async with async_playwright() as playwright:
        pages_found = await crawler.run_crawler(
            playwright, 
            job['url'], 
            job['globs'],
            max_concurrency=job.get('concurrency', 20), # Use 'concurrency' from job or default to 20
            url_normalization_rules=job.get('url_normalization_rules', {}),
            max_urls_to_find=max_pages
        )

        if dbupdates:
            print(f"      - inserting {len(pages_found)} url's in db for job: {job['job']}")
        try:
            # insert the pages
            for page in pages_found:
                if dbupdates:
                    db.insert_new_page(
                        normalized_url=page['normalized_url'],
                        original_url=page['original_url'],
                        title=page['title'],
                        job=job['job'],
                        tags=job['tags'],
                        workspaces=job['workspaces'],
                        image_urls=page['image_urls']
                    )
                else:
                    print(page['normalized_url'])
        except Exception as e:
            print(f"Error Encountered: {e}")


async def crawler_mode(args: argparse.ArgumentParser, db: DatabaseManager) -> None:
    """
    asynchronously calls the web crawler for specified or all jobs and commits all DB changes
    """
    print("\ncrawler mode\n")

    job_list = get_links_json()

    max_urls = args.maxurls

    run_specific_job = False
    if len(args.jobs) > 0:
        print("will perform specific job runs:")
        run_specific_job = True
        for argjob in args.jobs:
            for j in job_list:
                if "job" in j and j["job"] == argjob:
                    print(f" - Now processing job: {argjob}")
                    await crawl_site(db, j, max_urls, args.db_updates)
                    break
    
    # only perform the full job list if there were no jobs specified
    if run_specific_job == False:
        print("will perform a full job run")
        for job in job_list:
            await crawl_site(db, job, max_urls, args.db_updates)
    
    if args.db_updates:
        print(f"      - committing all changes in the DB")
        db.commit()
# endregion Crawler

# region Download
def download_page(db, page):
    """
    retrieves the core content as markdown from the page and updates the appropriate pages table row
    """
    
    db.set_site_config(page['normalized_url'])
    
    try:      
        markdown = scrape_to_markdown(
            page['original_url'],
            db.site_parent_element,
            db.site_child_element,
            db.site_base_url,
            page['tags'],
            page['job']
        )

        db.update_page(
            page_id=page['page_id'],
            content=markdown,
            status="scraped"
        )
    except Exception as e:
        print(f"Error Encountered: {e}")

def download(db, jobs):
    """
    calls get_web_markdown for all pages in 'new' status and updates the database
    """
    
    print("\nDownload mode\n")

    # get all new pages
    if len(jobs) > 0:
        for job in jobs:
            total_pages = db.get_pages_count(status="new", job=job)
            count = 0
            for page in db.get_pages(status="new", job=job):
                count += 1
                print(f"{count/total_pages*100:.1f}% Retrieving markdown for page: {page['normalized_url']}")
                download_page(db, page)
    else:
        total_pages = db.get_pages_count(status="new")
        count = 0
        for page in db.get_pages(status="new"):
            count += 1
            print(f"{count/total_pages*100:.1f}% Retrieving markdown for page: {page['normalized_url']}")
            download_page(db, page)

# endregion Download

# region Console

def console_print(args, db):
    """
    calls get_web_markdown for all pages in 'new' status and updates the database
    """
    i=0
    if args.print != "*":
        count_rows = db.get_pages_count(job=args.print)
        pages = db.get_pages(job=args.print)
        print(f"Job {args.print} has a total of {count_rows} pages")
    else:
        count_rows = db.get_pages_count()
        pages = db.get_pages()
        print(f"A total of {count_rows} in pages table")
    
    if args.maxurls is not None:
        print(f"showing the first {args.maxurls} pages")
    
    if isinstance(pages, sqlite3.Cursor):
        for page in pages:
            i += 1
            print(f"{i}: {page['normalized_url']}")
            if args.maxurls is not None and args.maxurls > 0 and i >= args.maxurls:
                break
# endregion Console

# region Upload
def upload_page(db: DatabaseManager, page: list, anythingllm_docs: list):
    """
    Uploads scraped content to anythingllm workspaces
    """
    try:
        if page["content_hash"] != page["uploaded_hash"]:
            print(f"    - page content change detected, re-uploading")
            
            anythingllm_filename = f"{page['job']}-{page['title']}"
            #print(f"current file name: {anythingllm_filename}")
            # move existing anythingllm doc to junk

            curdocs = []
            if anythingllm_docs:
                for doc in anythingllm_docs:
                    if doc.get("title") == anythingllm_filename:
                        #print(f"match: {doc.get("name")}")
                        curdocs.append(doc)
            
            if len(curdocs) > 0:
                print(f"    - Document exists, cleaning, deleting and re-uploading")

                for curdoc in curdocs:
                    # unlink the files from workspaces
                    delete_status = anythingllm_api.delete_anythingllm_files(
                        workspaces=page['workspaces'], 
                        foldername = page['job'], 
                        file_json_name = curdoc.get("name")
                    )
                    #print(delete_status)

                    # move anythingllm document to junk folder
                    filefrom = f"{page['job']}/{curdoc.get('name')}"
                    fileto = filefrom.replace(f"{page['job']}/",f"{junk_folder_name}/")
                    move_status = anythingllm_api.move_anythingllm_files(filefrom, fileto)
                    #print(move_status)
            
            # upload new version for embedding
            anythingllm_api.upload_to_anythingllm(
                workspaces=page['workspaces'],
                content=page['content'],
                anythingllm_folder=page['job'],
                anythingllm_filename=f"{page['job']}-{page['title']}"
            )

        # since the page was re-scraped, we always reset to uploaded status, even if the two hashes match (good version already uploaded)
        db.update_uploaded_page(
            page_id = page['page_id'],
            status="uploaded",
            uploaded_hash=page["content_hash"]
        )
    except Exception as e:
        print(f"Upload failed for page: {page['page_id']} with {e}")


def upload(db, jobs):
    """
    Gets documents should be uploaded and calls upload_page to upload to anythingllm
    """

    print("\n Upload Mode \n")

    # get all new pages
    if len(jobs) == 0:
        # no jobs passed, get all of them
        jobs = db.get_jobs()

    # make sure our junk folder exists
    # we move old pages to junk, and delete the junk folder after to kill the embeddings for the old document
    anythingllm_api.create_anythingllm_folder(junk_folder_name)
    
    for job in jobs:
        print(f"Processing pages for job: {job}")

        # get a list of all documents that exist in the anythingllm document folder
        response = anythingllm_api.get_anythingllm_files(job)
        anythingllm_docs = {} # initialize a blank list
        job_list = get_links_json()
        job_config = None
        for j in job_list:
            if job == j['job']:
                job_config = j
                break
        
        if job_config:
            workspaces = [s.strip() for s in job_config['workspaces'].split(',') if s.strip()]
        else:
            print(f'could not find job match..skipping: {job}')
            break

        # workspaces_docs = []
        # for w in workspaces:
        #     print(f"getting docs for workspace '{w}'")
        #     workspaces_docs.append(anythingllm_api.get_anythingllm_workspace_documents(w))

        # print(len(workspaces_docs))
        # for wd in workspaces_docs:
        #     print(wd.get('slug'))
        # quit()

        if "documents" in response:
            anythingllm_docs = response.get("documents", [])

        if len(anythingllm_docs) == 0:
            print(f"warning: 0 length list of documents from anythingllm!!")

        total_pages = db.get_pages_count(status="scraped", job=job)
        count = 0
        for page in db.get_pages(status="scraped", job=job):
            count += 1
            print(f" {count/total_pages*100:.1f}% - uploading page: {page["normalized_url"]}")
            upload_page(db, page, anythingllm_docs)
    
    # clear out the old items
    #anythingllm_api.delete_anythingllm_folder(junk_folder_name)

# endgion Upload

# endregion
# -----------------------------------------------------------
# endregion functions
# -----------------------------------------------------------

if __name__ == "__main__":
    # -----------------------------------------------------------
    # region Argparse Configuration
    # This section defines all command-line arguments for the script.
    # -----------------------------------------------------------

    # get the passed command line parameters
    parser = argparse.ArgumentParser(
        description="main rag data controller script to manage SQLite and AnythingLLM data.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-c", "--crawler",
        action="store_true",
        help="Enables crawler mode"
    )

    parser.add_argument(
        "-d", "--download",
        action="store_true",
        help="Enables content download mode. Must be run after crawler jobs have completed successfully"
    )

    parser.add_argument(
        "-db", "--db_updates",
        action="store_false",
        help=
    """    Bypasses all database updates in crawler mode only, and prints the updates to console. 
    By default, without this parameter, database updates will be performed.
    If this parameter is detected on the command line, database updates are NOT performed
    """
    )

    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help=
    """    Force flag to bypass certain check and force actions.
    Currently implemented;
        Crawler Mode:
          - ignore last database update, and will process crawler jobs no matter what
    """
    )

    parser.add_argument(
        "-j", "--jobs",
        type=lambda s: [item.strip() for item in s.split(',')], # Custom type to split by comma and strip whitespace
        default=[], # Default to an empty list if no jobs are provided
        help=
    """    A comma-separated list of crawler job names to process.
    if ommitted, all defined jobs will be processed

    NOTE: requires --crawler, --print, --download, or --upload
    
    Examples:
        --jobs cleanup,report,sync # no whitespaces
        --jobs "job1, job2, job3"  # allows whitespace seperation
    """
    )

    parser.add_argument(
        "--maxurls",
        type=int,
        default=None,
        help="maximum amount of pages for the crawler to return. requires --crawler or --print"
    )

    parser.add_argument(
        "-p", "--print",
        type=str,
        help="prints urls belonging to a crawler job to the console. specify a job name or '*' for all jobs"
    )

    parser.add_argument(
        "-u", "--upload",
        action="store_true",
        help=
        """    Upload mode. Uploads all pages (or pages of a specific job) that have been sraped to anythingllm workspaces

        """
    )

    args = parser.parse_args()

    # endregion
    # -----------------------------------------------------------
    # End Argparse Configuration
    # -----------------------------------------------------------

    db = DatabaseManager(DB_File)

    # parse through the args
    if args.crawler:
        if args.db_updates == False:
            print("\n NO DATABASE UPDATES WILL BE PERFORMED - OUTPUT TO CONSOLE\n")
        asyncio.run(crawler_mode(args, db))
    
    if args.download:
        download(db, args.jobs)

    if args.upload:
        upload(db, args.jobs)

    if args.print:
        console_print(args, db)

    db.close()