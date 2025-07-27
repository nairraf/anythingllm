import anythingllm_api
import os
import subprocess

ANYTHINGLLM_API_KEY = os.getenv("ANYTHINGLLM_API_KEY")
TAGS_MAP = {
    ".md": "type:md",
    ".cs": "type:cs",
    ".xaml": "type:xaml",
}

# Settings
REPO_PATH = "/home/ian/repos/selos"

def get_current_branch(repo_path):
    result = subprocess.run(
        ["git", "-C", repo_path, "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        raise RuntimeError(f"Error: {result.stderr.strip()}")


def collect_files(repo_path):
    for root, _, files in os.walk(repo_path):
        for file in files:
            filepath = os.path.join(root, file)
            ext = os.path.splitext(file)[-1].lower()
            if ext in TAGS_MAP:
                yield filepath, file, TAGS_MAP[ext]

def root_to_label(path):
    root_name = os.path.dirname(path).replace("/", "_").replace("\\", "_").strip("_")
    if root_name.startswith('_'):
        print(root_name)
        root_name = root_name[1:]
    return root_name


if __name__ == "__main__":
    git_branch = get_current_branch(REPO_PATH)
    if git_branch == "main":
        anythingllm_workspace = "selos-main"
    elif git_branch == "development":
        anythingllm_workspace = "selos-development"
    elif "feature" in git_branch:
        anythingllm_workspace = "selos-experiments"
    else:
        anythingllm_workspace = "test"

    tags = []

    for filepath, filename, tag in collect_files(REPO_PATH):
        # Clean file name to ensure uniqueness inside AnythingLLM
        #file_path = os.path.dirname(filepath).replace("/","_")
        #file_name = os.path.basename(filename)

        folder_safe = root_to_label(filepath.replace(REPO_PATH, ""))
        if folder_safe:
            llm_filename = f"{anythingllm_workspace}_{folder_safe}_{filename}".replace("/", "_")
        else:
            # elements with no parent folder don't have a folder_safe, so ommit it to resolve the __ problem in names
            llm_filename = f"{anythingllm_workspace}_{filename}".replace("/", "_")

        with open(filepath, "rb") as f:
            file_bytes = f.read()

        print(f"⬆️ Uploading {filename} to {llm_filename} with tag [{tag}]...")
        anythingllm_api.upload_to_anythingllm(
            workspace_slug=anythingllm_workspace,
            file=filename,
            file_bytes=file_bytes,
            tags=[tag, "source:local"],
            anythingllm_folder=f"git-{anythingllm_workspace}",
            anythingllm_filename=llm_filename
        )


