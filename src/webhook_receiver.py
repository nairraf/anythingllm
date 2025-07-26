import base64
from flask import Flask, abort, request, jsonify
from threading import Thread
import json
import hmac
import hashlib
import os
import requests

app = Flask(__name__)

GITHUB_SECRET = os.getenv("GITHUB_SELOS_SECRET").encode()  # Must be bytes
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

def verify_github_signature(payload, signature_header):
    # Remove "sha256=" prefix
    signature = signature_header.split('=')[1]
    # Create HMAC using the secret and payload
    mac = hmac.new(GITHUB_SECRET, msg=payload, digestmod=hashlib.sha256)
    expected = mac.hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected, signature)

def get_github_changes(owner, repo, before_sha, after_sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{before_sha}...{after_sha}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    data = response.json()

    changed_files = [f['filename'] for f in data.get('files', [])]
    return changed_files

def get_github_file(owner, repo, path, ref):
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    data = response.json()

    if data.get("encoding") == "base64":
        content = data["content"]
        return content
    else:
        return None
    
def upload_to_anythingllm(workspace_slug, file, file_bytes, tags, anythingllm_folder, anythingllm_filename):
    url = f"http://localhost:3001/api/v1/document/upload/{anythingllm_folder}"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    files = {"file": (anythingllm_filename, file_bytes)}
    
    data = {
        "addToWorkspaces": workspace_slug
    }

    response = requests.post(url, headers=headers, files=files, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def get_anythingllm_files(foldername):
    url = f"http://localhost:3001/api/v1/documents/folder/{foldername}"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def delete_anythingllm_files(workspacename, foldername, filename, file_json_name):
    success = False
    url = url = f"http://localhost:3001/api/v1/workspace/{workspacename}/update-embeddings"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    data = {
        "deletes": [
            f"{foldername}/{file_json_name}"
        ]
    }

    print(f"unlink {foldername}/{file_json_name} for workspace {workspacename}")
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        success = True


    return success

def update_anythingllm_pin(workspacename, foldername, filename, file_json_name):
    url = url = f"http://localhost:3001/api/v1/workspace/{workspacename}/update-pin"
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

    print(f"pining {foldername}/{file_json_name} in workspace {workspacename}: pinStatus: {pinstatus}")
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    if response.status_code == 200:
        print(response.json())
        return True
    return False

def create_anythingllm_folder(foldername):
    url = url = f"http://localhost:3001/api/v1/document/create-folder"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    data = {
        "name": foldername
    }

    print (f"creating folder {foldername}")
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return True
    return False

def delete_anythingllm_folder(foldername):
    url = url = f"http://localhost:3001/api/v1/document/remove-folder"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "application/json"
    }

    data = {
        "name": foldername
    }

    print (f"deleting folder {foldername}")
    response = requests.delete(url, headers=headers, json=data)
    if response.status_code == 200:
        print(response.json())
        return True
    return False

def move_anythingllm_files(from_json,to_json):
    url = url = f"http://localhost:3001/api/v1/document/move-files"
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

    print (f"moving from: {from_json} to: {to_json}")
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return True
    return False

def async_processor(data):
    # Log the received data
    tags = []

    ref = data.get("ref", "N/A")
    branch = ref.split("/")[-1]
    tags.append(f"branch:{branch}")
    tags.append(f"source:github")

    if branch == "main":
        anythingllm_workspace = "selos-main"
    elif branch == "development":
        anythingllm_workspace = "selos-development"
    elif "feature" in branch:
        anythingllm_workspace = "selos-experiments"

    owner_name = data.get("repository", {}).get("owner", {}).get("name", "Unknown")
    before_hash = data.get("before", "N/A")
    after_hash = data.get("after", "N/A")
    repo_name = data.get("repository", {}).get("name", "Unknown")
    # full_repo_name = data.get("repository", {}).get("full_name", "Unknown")
    
    #anythingllm_workspace = "test" # force to test when testing
    anythingllm_folder_name = f"git-{repo_name}-{branch}"
    
    # get the github changes files for this push
    files = get_github_changes(owner_name, repo_name, before_hash, after_hash)

    # get a list of all documents that exist in the anythingllm document folder
    response = get_anythingllm_files(anythingllm_folder_name)
    anythingllm_docs = {} # initialize a blank list

    if "documents" in response:
        anythingllm_docs = get_anythingllm_files(anythingllm_folder_name).get("documents", [])

    #print(anythingllm_docs)
    ## create anythingllm junk folder. you can't delete files, but you can move files, create folders and delete folders...
    ## so, for files that require re-indexing, we move the files to the junk folder, re-upload them, and after the run is done
    ## delete the junk folder which deletes the files
    junk_folder_name = "junk"
    create_anythingllm_folder(junk_folder_name)

    for f in files:
        if f.endswith(".cs"):
            tags.append(f"type:cs")
        elif f.endswith(".xaml"):
            tags.append(f"type:xaml")
        elif f.endswith(".md"):
            tags.append(f"type:md")
        else:
            continue
        
        file_path = os.path.dirname(f).replace("/","_")
        file_name = os.path.basename(f)
        anythingllm_filename = f"{anythingllm_folder_name.replace('git-','')}_{file_path}_{file_name}"

        docexists = False
        curdoc = {}
        if anythingllm_docs:
            print("looping through docs")
            for doc in anythingllm_docs:
                if doc.get("title") == anythingllm_filename:
                    docexists = True
                    curdoc = doc
                    break

        if docexists:
            print(f"Document {anythingllm_filename} exists, cleaning, deleting and re-uploading")
            # unlink the files from the workspace
            delete_anythingllm_files(anythingllm_workspace, anythingllm_folder_name, anythingllm_filename, curdoc.get("name"))
            filefrom = f"{anythingllm_folder_name}/{curdoc.get('name')}"
            fileto = filefrom.replace(f"git-{repo_name}-{branch}/",f"{junk_folder_name}/")
            move_anythingllm_files(filefrom, fileto)
        else:
            print(f"Document {anythingllm_filename} Doesn't Exist, uploading to workspace: {anythingllm_workspace}")
        

        raw_data = get_github_file(owner_name, repo_name, f, ref)
        response = upload_to_anythingllm(anythingllm_workspace,f, raw_data, tags, anythingllm_folder_name, anythingllm_filename)
        #print(response)
        if response:
            update_anythingllm_pin(anythingllm_workspace, anythingllm_folder_name, anythingllm_filename, response["documents"][0].get("name") )
        
    # cleanup junk
    delete_anythingllm_folder(junk_folder_name)
    print(f"Upload and Index for {anythingllm_folder_name}/{anythingllm_filename} in {anythingllm_workspace} Complete")



@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        signature_header = request.headers.get('X-Hub-Signature-256')
        if not signature_header:
            abort(400, 'Missing signature header')
        
        payload = request.data
        if not verify_github_signature(payload, signature_header):
            abort(403, 'Invalid signature')

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        thread = Thread(target=async_processor, args=(data,))
        thread.start()

        return jsonify({"message": "Webhook received"}), 200
    return jsonify({"error": "Invalid request"}), 400

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
