from db import DatabaseManager
from urllib.parse import urlparse
from get_web_markdown import scrape_to_markdown
import anythingllm_api

DB_File = r'..\..\db\sites.db'

db = DatabaseManager(DB_File)

# db.insert_site(
#     "https://learn.microsoft.com",
#     'div[data-main-column]',
#     'div.content',
#     "Microsoft Learn"
# )
#
#db.commit()


db.set_site_config('learn.microsoft.com')


# print (f"scraping '{url}' with site config: {db.site_name}")
# markdown = scrape_to_markdown(url, db.site_parent_element, db.site_child_element, db.site_base_url)
# print (f"scraping completed, updating database")
# db.insert_page(
#     url=url,
#     content=markdown,
#     status="test"
# )
#db.commit()

new_sites = db.get_pages()

for site in new_sites:
    print(f"""
        Updating the following page to complete:
        
        page_id: {site['page_id']}
        url: {site['url']}
        status: {site['status']}
    """)
    api_url = urlparse(site['url'])
    basename = api_url.netloc
    
    anythingllm_folder = f"{site['category']}"
    filename=f"{api_url.netloc}-{(api_url.path).replace('/','_')}{(api_url.query)}"
    anythingllm_filename = f"{anythingllm_folder}-{filename}"

    try:
        anythingllm_api.upload_to_anythingllm(
            workspace_slug=site['workspaces'],
            content=site['content'],
            anythingllm_folder=anythingllm_folder,
            anythingllm_filename=anythingllm_filename
        )
        db.update_page_status(site['page_id'])
    except:
        print("that failed")



# anythingllm_api.upload_to_anythingllm(
#     workspace_slug=anythingllm_workspace,
#     file=filename,
#     file_bytes=file_bytes,
#     tags=[tag, "source:local"],
#     anythingllm_folder=f"git-{anythingllm_workspace}",
#     anythingllm_filename=llm_filename
# )



db.close()