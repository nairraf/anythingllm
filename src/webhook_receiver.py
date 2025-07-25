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
    
def upload_to_anythingllm(workspace_slug, file_path, file_bytes, tags):
    url = f"http://localhost:3001/api/v1/document/raw-text"
    headers = {
        "Authorization": f"Bearer {ANYTHINGLLM_API_KEY}",
        "Accept": "appliation/json"
    }

    
    data = {
        "textContent": file_bytes,
        "addToWorkspaces": workspace_slug,
        "metadata": {
            "title": tags["alt_name"],
            "docAuthor": "Ian",
            "docsource": "Github"
        }
    }

    response = requests.post(url, headers=headers, json=data)
    return response

def async_processor(data):
    # Log the received data
    tags = {}

    ref = data.get("ref", "N/A")
    branch = ref.split("/")[-1]
    tags["branch"]=branch
    tags["source"]="github"

    if branch == "main":
        anythingllm_workspace = "selos-main"
    elif branch == "development":
        anythingllm_workspace = "selos"

    owner_name = data.get("repository", {}).get("owner", {}).get("name", "Unknown")
    before_hash = data.get("before", "N/A")
    after_hash = data.get("after", "N/A")
    repo_name = data.get("repository", {}).get("name", "Unknown")
    # full_repo_name = data.get("repository", {}).get("full_name", "Unknown")
    
    files = get_github_changes(owner_name, repo_name, before_hash, after_hash)
    for f in files:
        if f.endswith(".cs"):
            tags["type"]="cs"
        elif f.endswith(".xaml"):
            tags["type"]="xaml"
        elif f.endswith(".md"):
            tags["type"]="md"
        else:
            continue
        
        tags["alt_name"]=f.replace("/","_")
        raw_data = get_github_file(owner_name, repo_name, f, ref)
        
        print(raw_data)

        anythingllm_workspace = "test" # force to test when testing
        print(f"uploading file: {f} to workspace {anythingllm_workspace} with tags {tags}")

        response = upload_to_anythingllm(anythingllm_workspace,f, raw_data, tags)

        print(f"Upload response status: {response.status_code}")
        #print(f"Upload response content: {response.text}")


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
