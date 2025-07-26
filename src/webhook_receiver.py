import base64
from flask import Flask, abort, request, jsonify
from threading import Thread
import json
import hmac
import hashlib
import os
import requests
import logging

from anythingllm_api import create_anythingllm_folder, delete_anythingllm_files, delete_anythingllm_folder, get_anythingllm_files, move_anythingllm_files, update_anythingllm_pin, upload_to_anythingllm

app = Flask(__name__)

GITHUB_SECRET = os.getenv("GITHUB_SELOS_SECRET").encode()  # Must be bytes
GITHUB_TOKEN = os.getenv("GITHUB_API_KEY")
ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")

logging.basicConfig(
    filename='/home/ian/github_webhook.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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

    #logging.info(anythingllm_docs)

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
            logging.info("looping through docs")
            for doc in anythingllm_docs:
                if doc.get("title") == anythingllm_filename:
                    docexists = True
                    curdoc = doc
                    break

        if docexists:
            logging.info(f"Document {anythingllm_filename} exists, cleaning, deleting and re-uploading")
            # unlink the files from the workspace
            delete_anythingllm_files(anythingllm_workspace, anythingllm_folder_name, anythingllm_filename, curdoc.get("name"))
            filefrom = f"{anythingllm_folder_name}/{curdoc.get('name')}"
            fileto = filefrom.replace(f"git-{repo_name}-{branch}/",f"{junk_folder_name}/")
            move_anythingllm_files(filefrom, fileto)
        else:
            logging.info(f"Document {anythingllm_filename} Doesn't Exist, uploading to workspace: {anythingllm_workspace}")
        

        raw_data = get_github_file(owner_name, repo_name, f, ref)
        response = upload_to_anythingllm(anythingllm_workspace,f, raw_data, tags, anythingllm_folder_name, anythingllm_filename)
        #logging.info(response)
        if response:
            update_anythingllm_pin(anythingllm_workspace, anythingllm_folder_name, anythingllm_filename, response["documents"][0].get("name") )
        
    # cleanup junk
    delete_anythingllm_folder(junk_folder_name)
    logging.info(f"Upload and Index for {anythingllm_folder_name}/{anythingllm_filename} in {anythingllm_workspace} Complete")



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
