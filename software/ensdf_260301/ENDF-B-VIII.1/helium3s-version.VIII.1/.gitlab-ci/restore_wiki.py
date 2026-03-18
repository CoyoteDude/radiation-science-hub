# -*- coding: utf-8 -*-
"""
Created on Thu Oct  5 10:28:03 2023

@author: rcoles
"""

import os
import requests

# Your GitLab personal access token, GitLab URL, and other configuration
gitlab_token = os.environ.get('WIKI_ACCESS_TOKEN') # Use the CI_JOB_TOKEN provided by GitLab
gitlab_url = "https://git.nndc.bnl.gov/api/v4"
project_id = os.getenv("CI_PROJECT_ID")
repository_name = os.getenv("CI_PROJECT_NAME")
branch_name = "backup-wiki-pages"  # Choose a branch name for storing backups

# Function to restore wiki pages
def restore_wiki_pages(project_id, branch_name):
    # Get the list of backup files in the repository
    repository_files_url = f"{gitlab_url}/projects/{project_id}/repository/tree?ref={branch_name}"
    response = requests.get(repository_files_url, headers={"PRIVATE-TOKEN": gitlab_token})

    if response.status_code == 200:
        files = response.json()
        for file in files:
            if file["type"] == "blob" and file["name"].endswith(".md"):
                file_name = file["name"]
                # Get the content of the backup file
                get_file_url = f"{gitlab_url}/projects/{project_id}/repository/files/{file_name}/raw?ref={branch_name}"
                response = requests.get(get_file_url, headers={"PRIVATE-TOKEN": gitlab_token})

                if response.status_code == 200:
                    page_title = file_name[:-3]  # Remove ".md" extension
                    page_content = response.text
                    # Create or update the wiki page
                    wiki_page_url = f"{gitlab_url}/projects/{project_id}/wikis/{page_title}"
                    data = {"title": page_title, "content": page_content}
                    response = requests.put(wiki_page_url, headers={"PRIVATE-TOKEN": gitlab_token}, json=data)

                    if response.status_code == 201:
                        print(f"Restored page for {page_title}")
                    elif response.status_code == 200:
                        print(f"Updated page for {page_title}")
                    else:
                        print(f"Failed to restore/update page for {page_title}")
                else:
                    print(f"Failed to get content for file {file_name}")
    else:
        print("Failed to retrieve repository files.")

# Restore wiki pages from the repository
restore_wiki_pages(project_id, branch_name)

