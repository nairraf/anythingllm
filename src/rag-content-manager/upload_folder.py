import argparse
import glob
import json
import os
from pathlib import Path
import textwrap
import anythingllm_api

# Define the path to the json job links configuration file
JOBS_FILE = './upload_folder_jobs.json'

def find_files(base_dir, glob_patterns):
    """
    returns all files for a given base_dir recursively matching the glob patterns
    """
    for pattern in glob_patterns:
        full_pattern = os.path.join(base_dir, pattern)
        for filename in glob.glob(full_pattern, recursive=True):
            yield filename

def get_jobs() -> list[dict]:
    """
    retrieves the list of jobs from the crawler_jobs.json file
    """
    jobs = []
    try:
        # Read the links configuration file
        with open(JOBS_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()
        jobs = json.loads(file_content)
        return jobs
    except FileNotFoundError:
        print(f"Error: Config file '{JOBS_FILE}' not found.")
        exit(1) # Exit if the config file is missing
    except json.JSONDecodeError as e:
        print(f"Error parsing config file '{JOBS_FILE}': {e}")
        exit(1) # Exit if the JSON is malformed
    except Exception as e:
        print(f"Error reading config file: {e}")
        exit(1)

def runjob(job):
    """
    runs a specific filesystem upload job
    """

    print(f"running job: {job['job']}")

    # get a list of all documents that exist in the anythingllm document folder
    response = anythingllm_api.get_anythingllm_files(job['anythingllm_folder'])
    anythingllm_docs = {} # initialize a blank list

    if "documents" in response:
        anythingllm_docs = response.get("documents", [])

    ## create anythingllm junk folder. you can't delete files, but you can move files, create folders and delete folders...
    ## so, for files that require re-indexing, we move the files to the junk folder, re-upload them, and after the run is done
    ## delete the junk folder which deletes the files
    junk_folder_name = "junk"
    anythingllm_api.create_anythingllm_folder(junk_folder_name)

    local_fs_path = Path(job['local_folder'])
    root_folder_name = local_fs_path.name

    for file in find_files(local_fs_path, job['globs']):
        relative_file_path = file.replace(f'{local_fs_path}','')
        filename = os.path.basename(relative_file_path)
        parent_names = [p.name for p in Path(relative_file_path).parents if p.name]
        parents_str = '_'.join(reversed(parent_names))

        if parents_str:
            anythingllm_filename=(f"{root_folder_name}_{parents_str}_{filename}")
        else:
            anythingllm_filename=(f"{root_folder_name}_{filename}")

        ## see if there is a file in anythingllm by that name
        docexists = False
        curdoc = {}
        if anythingllm_docs:
            for doc in anythingllm_docs:
                if doc.get("title") == anythingllm_filename:
                    docexists = True
                    curdoc = doc
                    break
        
        ## move to junk if it exists
        if docexists:
            print(f"Document {anythingllm_filename} exists, cleaning, deleting and re-uploading")
            # unlink the files from the workspace
            anythingllm_api.delete_anythingllm_files(job['workspaces'], job['anythingllm_folder'], curdoc.get("name"))
            filefrom = f"{job['anythingllm_folder']}/{curdoc.get('name')}"
            fileto = filefrom.replace(f"{job['anythingllm_folder']}/",f"{junk_folder_name}/")
            anythingllm_api.move_anythingllm_files(filefrom, fileto)
        else:
            print(f"Document {anythingllm_filename} Doesn't Exist, uploading to workspace: {job['anythingllm_folder']}")

        ## upload the new file
        with open(file, "rb") as f:
            file_bytes = f.read()

        metadata = f"""
            #---
            #filename: {filename}
            #path: {relative_file_path}
            #tags: {job['tags']}
            #job: {job['job']}
            #---
        """
        metadata_bytes = metadata.encode('utf-8')
        file_bytes = metadata_bytes + file_bytes

        print(f"⬆️ Uploading {filename} to {anythingllm_filename}...")
        response = anythingllm_api.upload_to_anythingllm(
            workspaces=job['workspaces'],
            content=file_bytes,
            anythingllm_folder=job['anythingllm_folder'],
            anythingllm_filename=anythingllm_filename
        )

        uploaded_file_name = response.get("documents", [])[0].get('name')
        # check if we should pin this document:
        for file,workspaces in job['pins'].items():

            if relative_file_path.lower() == str(Path(file)).lower():
                for w in workspaces:
                    print(f"Updating pins for file: {file} in workspaces: {w}")
                    anythingllm_api.update_anythingllm_pin(
                        workspacename=w,
                        foldername=job['anythingllm_folder'],
                        file_json_name=uploaded_file_name,
                        pinstatus=True
                    )
                break

    # clear out the old items
    anythingllm_api.delete_anythingllm_folder(junk_folder_name)


if __name__ == "__main__":
    # get the passed command line parameters
    parser = argparse.ArgumentParser(
        description="local folder uploader to anythingllm",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "-j", "--jobs",
        type=lambda s: [item.strip() for item in s.split(',')], # Custom type to split by comma and strip whitespace
        default=[], # Default to an empty list if no jobs are provided
        help="comma seperated list of job names to run. job names are defined in the json file"
    )

    args = parser.parse_args()

    job_list = get_jobs()

    if len(args.jobs) > 0:
        print("running specific jobs")
        for job in args.jobs:
            for jl in job_list:
                if job == jl['job']:
                    runjob(jl)
    else:
        print("running all jobs")
        for jl in job_list:
            runjob(jl)