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
url = "https://learn.microsoft.com/en-us/dotnet/maui/?view=net-maui-9.0"
api_url = urlparse(url)
basename = api_url.netloc


db.set_site_config(basename)


print (f"scraping '{url}' with site config: {db.site_name}")
markdown = scrape_to_markdown(url, db.site_parent_element, db.site_child_element, db.site_base_url)
print (f"scraping completed, updating database")
db.insert_page(
    url=url,
    content=markdown,
    status="test"
)



# anythingllm_api.upload_to_anythingllm(
#     workspace_slug=anythingllm_workspace,
#     file=filename,
#     file_bytes=file_bytes,
#     tags=[tag, "source:local"],
#     anythingllm_folder=f"git-{anythingllm_workspace}",
#     anythingllm_filename=llm_filename
# )


db.commit()
db.close()