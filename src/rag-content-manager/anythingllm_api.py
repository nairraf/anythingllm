import os
import requests
import logging

GITHUB_SECRET = os.getenv("GITHUB_SELOS_SECRET").encode()  # Must be bytes
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

def upload_to_anythingllm(workspace_slug, file, file_bytes, tags, anythingllm_folder, anythingllm_filename):
    url = f"https://aura.farrworks.com/api/v1/document/upload/{anythingllm_folder}"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    files = {"file": (anythingllm_filename, file_bytes)}
    
    data = {
        "addToWorkspaces": workspace_slug
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    logging.info(f"upload_to_anythingllm status code: {response.status_code}")
    if response.status_code == 200:
        return response.json()
    else:
        return {}

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

def delete_anythingllm_files(workspacename, foldername, filename, file_json_name):
    success = False
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

    logging.info(f"unlink {foldername}/{file_json_name} for workspace {workspacename}")
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        success = True


    return success

def update_anythingllm_pin(workspacename, foldername, filename, file_json_name):
    url = url = f"https://aura.farrworks.com/api/v1/workspace/{workspacename}/update-pin"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    pinned_filename = [
        "README.md",
        "technologies.md",
        "PROJECT_PLAN.md"
    ]

    pinstatus = False
    for f in pinned_filename:
        if f in filename:
            pinstatus = True
            break
    
    data = {
        "docPath": f"{foldername}/{file_json_name}",
        "pinStatus": pinstatus
    }

    logging.info(f"pining {foldername}/{file_json_name} in workspace {workspacename}: pinStatus: {pinstatus}")
    response = requests.post(url, headers=headers, json=data)
    logging.info(f"update_anythingllm_pin response code {response.status_code}")
    if response.status_code == 200:
        return True
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

    logging.info(f"moving from: {from_json} to: {to_json}")
    response = requests.post(url, headers=headers, json=data)
    logging.info(f"move_anythingllm_files response code {response.status_code}")
    if response.status_code == 200:
        return True
    return False