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
    return os.path.dirname(path).replace("/", "_").replace("\\", "_").strip("_")


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
        folder_safe = root_to_label(filepath.replace(REPO_PATH, ""))
        llm_filename = f"{folder_safe}_{filename}".replace(" ", "_").replace("/", "_")

        with open(filepath, "rb") as f:
            file_bytes = f.read()

        print(f"⬆️ Uploading {filename} with tag [{tag}]...")
        anythingllm_api.upload_to_anythingllm(
            workspace_slug=anythingllm_workspace,
            file=filename,
            file_bytes=file_bytes,
            tags=[tag, "source:local"],
            anythingllm_folder=f"git-{anythingllm_workspace}",
            anythingllm_filename=llm_filename
        )


