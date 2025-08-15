import json
import os
import requests
import logging

GITHUB_SECRET = os.getenv("GITHUB_SELOS_SECRET").encode()  # Must be bytes
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

def upload_to_anythingllm(workspace_slug, content, anythingllm_folder, anythingllm_filename):
    url = f"https://aura.farrworks.com/api/v1/document/upload/{anythingllm_folder}"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    files = {"file": (anythingllm_filename, content)}
    
    data = {
        "addToWorkspaces": workspace_slug
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    logging.info(f"upload_to_anythingllm status code: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def upload_link(link, url, workspaces):
    url = f"http://localhost:3001/api/v1/document/upload-link"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    json_data = {
        "link": url,
        "addToWorkspaces": workspaces
    }

    print(f"scraping site {link}")
    response = requests.post(url, headers=headers, json=json_data)
    print(f"scrape status code: {response.status_code}")
    if response.status_code == 200:
        return True
    return False

def upload_to_anythingllm_rawtext(workspace_slug, content, title, url, description):
    url = f"http://localhost:3001/api/v1/document/raw-text"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    json_data = {
        "textContent": content,
        "addToWorkspaces": workspace_slug,
        "metadata": {
            "title": title,
            "docSource": url,
            "description": description
        }
    }

    response = requests.post(url, headers=headers, json=json_data)
    print(f"scrape status code: {response.status_code}")
    if response.status_code == 200:
        return True
    return False

def get_anythingllm_files(foldername):
    url = f"https://aura.farrworks.com/api/v1/documents/folder/{foldername}"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    logging.info(f"get_anythingllm_files status code: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def delete_anythingllm_files(workspaces, foldername, file_json_name):
    success = False
    # the file could be embeded in many workspaces, we clear all of them
    # workspaces is defined as comma seperated in the json jobs lists
    workspace_list = workspaces.split(",")

    for workspacename in workspace_list:
        url = url = f"https://aura.farrworks.com/api/v1/workspace/{workspacename}/update-embeddings"
        headers = {
            "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
            "Accept": "application/json"
        }

        data = {
            "deletes": [
                f"{foldername}/{file_json_name}"
            ]
        }

        #print(f"unlink {foldername}/{file_json_name} for workspace {workspacename}")
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            #print(response)
            success = True

    return success

def update_anythingllm_pin(workspacename, foldername, file_json_name, pinstatus):
    url = url = f"https://aura.farrworks.com/api/v1/workspace/{workspacename}/update-pin"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }
    
    data = {
        "docPath": f"{foldername}/{file_json_name}",
        "pinStatus": pinstatus
    }

    #print(f"pining {foldername}/{file_json_name} in workspace {workspacename}: pinStatus: {pinstatus}")
    response = requests.post(url, headers=headers, json=data)
    #print(f"update_anythingllm_pin response code {response.status_code}")
    if response.status_code == 200:
        return True
    else:
        print(response)
    return False

def create_anythingllm_folder(foldername):
    url = url = f"https://aura.farrworks.com/api/v1/document/create-folder"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    data = {
        "name": foldername
    }

    logging.info(f"creating folder {foldername}")
    response = requests.post(url, headers=headers, json=data)
    logging.info(f"create_anythingllm_folder response code {response.status_code}")
    if response.status_code == 200:
        return True
    return False

def delete_anythingllm_folder(foldername):
    url = url = f"https://aura.farrworks.com/api/v1/document/remove-folder"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    data = {
        "name": foldername
    }

    logging.info(f"deleting folder {foldername}")
    response = requests.delete(url, headers=headers, json=data)
    logging.info(f"delete_anythingllm_folder response code {response.status_code}")
    if response.status_code == 200:
        return True
    return False

def move_anythingllm_files(from_json,to_json):
    url = url = f"https://aura.farrworks.com/api/v1/document/move-files"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    data = {
        "files": [
            {
                "from": from_json,
                "to": to_json
            }
        ]
    }

    print(f"moving from: {from_json} to: {to_json}")
    response = requests.post(url, headers=headers, json=data)
    logging.info(f"move_anythingllm_files response code {response.status_code}")
    if response.status_code == 200:
        return True
    return False