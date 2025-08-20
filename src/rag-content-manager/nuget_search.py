import requests

def get_all_maui_packages():
    base_url = "https://azuresearch-usnc.nuget.org/query"
    params = {
        "q": "maui",
        "skip": 0,
        "take": 100,  # max per request
        "prerelease": "false",
        "framework": "net9.0",
    }
    all_packages = []
    while True:
        resp = requests.get(base_url, params=params)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", [])
        if not results:
            break
        all_packages.extend(results)
        print(f"Fetched {len(results)} packages (total so far: {len(all_packages)})")
        if len(results) < params["take"]:
            break
        params["skip"] += params["take"]
    return all_packages

pkgs = get_all_maui_packages()
print(f"Found {len(pkgs)} MAUI packages.")

# Extract URLs
nuget_urls = [f"https://www.nuget.org/packages/{pkg['id']}" for pkg in pkgs]
for url in nuget_urls[:100]:
    print(url)