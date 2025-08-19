import argparse
import glob
import hashlib
import json
import os
from pathlib import Path
import textwrap
import anythingllm_api
from git import Repo
import platform
from db import DatabaseManager

# where the SQLite database resides
DB_File = Path('../../db/sites.db')

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
    retrieves the list of jobs from the JOBS_FILE
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

def get_os_name():
    os_name = platform.system().lower()
    if "windows" in os_name:
        return "windows"
    elif "linux" in os_name:
        return "linux"
    elif "darwin" in os_name:
        return "mac"
    else:
        return "other"

def get_file_hash(file_bytes):
    """
    Computes SHA256 hash of a bytes object.
    Returns the hex digest string.
    """
    sha = hashlib.sha256()
    sha.update(file_bytes)
    return sha.hexdigest()

def runjob(job, args, db):
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
    junk_folder_name = "JUNK"
    anythingllm_api.create_anythingllm_folder(junk_folder_name)

    detected_os = get_os_name()
    local_fs_path = None
    if detected_os == 'windows':
        local_fs_path = Path(job['local_folder']['windows'])
    
    if detected_os == 'linux':
        local_fs_path = Path(job['local_folder']['linux'])
    
    if local_fs_path == None:
        print('Error: could not detect OS!')
        quit()
    
    root_folder_name = local_fs_path.name
    print(f"- Detected OS: {detected_os}, local_path: {local_fs_path}")

    #quit()
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

        ## get file content and compute current hash
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
        file_hash = get_file_hash(file_bytes)

        print(f"⬆️ Uploading {filename} to '{anythingllm_filename}'")

        uploaded_file = db.get_file(job['anythingllm_folder'], anythingllm_filename)
 
        if uploaded_file:
            # compare file hashes to see if we need to re-upload
            if file_hash == uploaded_file["uploaded_hash"]:
                print("  - file hashes are the same, skipping anythingllm upload")
                continue
        
        ## we are doing the upload, check if the file exits and move to junk to prepare for new upload
        if docexists:
            if args.skip:
                print(f"  - Document {anythingllm_filename} exists, skipping due to --skip flag")
                continue

            print(f"  - Document {anythingllm_filename} exists, cleaning, deleting and re-uploading")
            # unlink the files from the workspace and move to the junk folder
            anythingllm_api.delete_anythingllm_files(job['workspaces'], job['anythingllm_folder'], curdoc.get("name"))
            filefrom = f"{job['anythingllm_folder']}/{curdoc.get('name')}"
            fileto = filefrom.replace(f"{job['anythingllm_folder']}/",f"{junk_folder_name}/")
            anythingllm_api.move_anythingllm_files(filefrom, fileto)
        else:
            print(f"  - Document {anythingllm_filename} Doesn't Exist, uploading to workspace: {job['anythingllm_folder']}")

        response = anythingllm_api.upload_to_anythingllm(
            workspaces=job['workspaces'],
            content=file_bytes,
            anythingllm_folder=job['anythingllm_folder'],
            anythingllm_filename=anythingllm_filename
        )

        if response:
            print("  - file uploaded successfully")
            db.insert_file(
                uploaded_hash = file_hash,
                anythingllm_folder = job['anythingllm_folder'],
                anythingllm_file_name = anythingllm_filename, 
                original_file_name = filename,
                status = "uploaded"
            )
            
            uploaded_file_name = response.get("documents", [])[0].get('name')
            # check if we should pin this document:
            for file,workspaces in job['pins'].items():
                if relative_file_path.lower() == str(Path(file)).lower():
                    for w in workspaces:
                        w = w.strip()
                        print(f"  - Updating pins for file: {file} in workspaces: '{w}'")
                        print(f"     - pin file_path: {uploaded_file_name}")
                        anythingllm_api.update_anythingllm_pin(
                            workspacename=w,
                            foldername=job['anythingllm_folder'],
                            file_json_name=uploaded_file_name,
                            pinstatus=True
                        )
                    break
        else:
            print(f"  - !! Error uploading file {anythingllm_filename} to {job['anythingllm_folder']}")

    # clear out the old items
    anythingllm_api.delete_anythingllm_folder(junk_folder_name)


if __name__ == "__main__":
    db = DatabaseManager(DB_File)

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

    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="displays all configured jobs and then exits. cannot be used with any other option"
    )

    parser.add_argument(
        "-s", "--skip",
        action="store_true",
        help=
        """    skips upload if file with same name is already uploaded
        This changes the default behaviour of deleting and overwriting the file
        """

    )

    args = parser.parse_args()

    job_list = get_jobs()

    if args.list:
        header = "Configured Jobs"
        print(f"\n{header}")
        print("-"*len(header))
        for j in job_list:
            print(j['job'])
        quit()

    if len(args.jobs) > 0:
        print("running specific jobs")
        for job in args.jobs:
            for jl in job_list:
                if job == jl['job']:
                    runjob(jl, args, db)
    else:
        print("running all jobs")
        for jl in job_list:
            runjob(jl, args, db)