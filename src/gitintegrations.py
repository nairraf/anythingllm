import requests
import glob
import os
from git import Repo
Repo.clone_from("git@github.com:nairraf/selos.git", '/home/ian/repos/selos')

## TODO: do this for dev, main, and feature branches

files = glob.glob('/home/ian/repos/selos/**/*.cs', recursive=True)
files += glob.glob('/home/ian/repos/selos/**/*.xaml', recursive=True)
files += glob.glob('/home/ian/repos/selos/**/*.md', recursive=True)

def get_tags(file_path):
    tags = []

    if "main" in file_path:
        tags.append("branch:main")
    elif "dev" in file_path:
        tags.append("branch:dev")
    elif "feature" in file_path:
        tags.append("branch:feature")

    if file_path.endswith('.cs'):
        tags.append("type:csharp")
    elif file_path.endswith('.xaml'):
        tags.append("type:xaml")
    elif file_path.endswith('.md'):
        tags.append("type:markdown")

for file in files:
    with open(file, 'r') as f:
        tags = get_tags(file)
        response = requests.post(
            "http://localhost:3001/v1/document/upload/selos-dev",
            headers={"Authorization": f"Bearer {os.getenv("ANYTHINGLLM_API_KEY")}"},
            files={"file": f},
            data={"tags[]": tags}
        )

