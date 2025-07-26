import os
import requests

ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

def upload_link(link, json_data):
    url = f"http://localhost:3001/api/v1/document/upload-link"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    print(f"scraping site {link}")
    response = requests.post(url, headers=headers, json=json_data)
    print(f"scrape status code: {response.status_code}")
    if response.status_code == 200:
        return True
    return False


dotnet_maui_links = [
    "https://learn.microsoft.com/en-us/dotnet/maui/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-maui-9.0&preserve-view=true",
    "https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-9/overview",
    "https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-9/sdk",
    "https://learn.microsoft.com/en-us/dotnet/fundamentals/",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-9.0",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-maui-9.0",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-maui-10.0",
    "https://learn.microsoft.com/en-us/dotnet/api/?view=net-10.0",
    "https://learn.microsoft.com/en-us/dotnet/maui/whats-new/dotnet-10?view=net-maui-9.0",
    "https://github.com/dotnet/maui/releases",
    "https://devblogs.microsoft.com/dotnet/category/maui/",
    "https://amarozka.dev/whats-new-dotnet-maui-2025/",
    "https://www.telerik.com/maui-ui/resources",
    "https://github.com/jsuarezruiz/awesome-dotnet-maui",
    "https://learn.microsoft.com/en-us/dotnet/maui/get-started/resources?view=net-maui-9.0"
]

for link in dotnet_maui_links:
    data = {
        "link": link,
        "addToWorkspaces": "test,selos-main,selos-development,selos-experiments"
    }
    upload_link(link, data)

