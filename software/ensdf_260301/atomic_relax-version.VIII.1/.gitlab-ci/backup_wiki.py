# -*- coding: utf-8 -*-
"""
Created on Thu Oct  5 10:25:25 2023

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

# Function to backup wiki pages
def backup_wiki_pages(project_id, branch_name):
    # Get the list of wiki pages
    wiki_pages_url = f"{gitlab_url}/projects/{project_id}/wikis"
    response = requests.get(wiki_pages_url, headers={"PRIVATE-TOKEN": gitlab_token})

    if response.status_code == 200:
        wiki_pages = response.json()
        for page in wiki_pages:
            page_title = page["title"]
            page_content = page["content"]
            # Push the backup data to the repository directly
            push_data_url = f"{gitlab_url}/projects/{project_id}/repository/files/{page_title}.md"
            data = {
                "branch": branch_name,
                "content": page_content,
                "commit_message": f"Backup wiki page '{page_title}'"
            }
            response = requests.put(push_data_url, headers={"PRIVATE-TOKEN": gitlab_token}, json=data)

            if response.status_code == 201 or response.status_code == 200:
                print(f"Backup completed for {page_title}")
            else:
                print(f"Failed to backup page {page_title}")

        # Push the changes to the branch
        push_branch_url = f"{gitlab_url}/projects/{project_id}/repository/branches/{branch_name}/push"
        response = requests.post(push_branch_url, headers={"PRIVATE-TOKEN": gitlab_token})

        if response.status_code == 200:
            print(f"Backups saved to the '{branch_name}' branch of '{repository_name}' repository.")
        else:
            print(f"Failed to push changes to branch {branch_name} in repository {repository_name}.")
    else:
        print("Failed to retrieve wiki pages.")

# Backup wiki pages for the project
backup_wiki_pages(project_id, branch_name)