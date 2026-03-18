# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 13:27:14 2023

@author: rcoles
"""

import requests
import csv
import yaml
import json
import os
import numpy as np
from datetime import datetime
from tabulate import tabulate
from urllib.parse import quote

# Define Constants
GITLAB_URL = "https://git.nndc.bnl.gov"
PROJECT_ID = "27"
ROOT_WIKI_SLUG = "Neutron-Artifacts"
ACCESS_TOKEN = os.environ.get('WIKI_ACCESS_TOKEN')
CSV_FILE_PATH = "/builds/endf/library/neutrons/.gitlab-ci/neutrons.csv"

# Function to update or create a nested Wiki page
def create_or_update_nested_wiki_page(page_title, updated_content, root_wiki = False):
    url = ""
    if root_wiki == False:
        url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{ROOT_WIKI_SLUG}%2F{page_title}"
        headers = {"PRIVATE-TOKEN": ACCESS_TOKEN, "Content-Type": "application/json"}
    else:
        url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{ROOT_WIKI_SLUG}"
        headers = {"PRIVATE-TOKEN": ACCESS_TOKEN, "Content-Type": "application/json"}

    # Check if the page already exists
    response = requests.get(url, headers=headers)
    print("Gitlab response status code: " + str(response.status_code))

    if response.status_code == 200:
        # Page exists, so update it
        print("Updating: " + str(url))
        old_content = response.json().get('content')
        if root_wiki == False:
            slug = f"{ROOT_WIKI_SLUG}/{page_title}"
            updated_data = {
                "title": page_title,
                "content": updated_content + str(old_content),
                "format": "markdown",
                "slug": slug,
                'encoding': 'UTF-8'
                }
            response = requests.put(url, headers=headers, json=updated_data)
            action = "updated"
        else:
            updated_data = {
                "title": ROOT_WIKI_SLUG,
                "content": updated_content + str(old_content),
                "format": "markdown",
                'encoding': 'UTF-8'
                }
            response = requests.put(url, headers=headers, json=updated_data)
            action = "updated"
    else:
        # Page does not exist, so create it
        slug = f"{ROOT_WIKI_SLUG}/{page_title}"
        print("Creating: " + str(url))
        if root_wiki == False:
            data = {
                "title": slug,
                "content": "None",
                "format": "markdown",
                "slug": slug,
                'encoding': 'UTF-8'
            }
            url_create = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis"
            response = requests.post(url_create, headers=headers, json=data)
            action = "created"
        else:
            data = {
                "title": f"{ROOT_WIKI_SLUG}",
                "content": updated_content,
                "format": "markdown",
                'encoding': 'UTF-8'
            }
            response = requests.post(url, headers=headers, json=data)
            action = "created"

    if response.status_code in [200, 201]:
        print(f"Nested Wiki page '{page_title}' {action} successfully.")
    else:
        print(f"Failed to {action} nested wiki page. Status code: {response.status_code}")
        print(response.text)


def get_wiki_page_content(wiki_path):
    url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{wiki_path}"
    headers = {
        "PRIVATE-TOKEN": ACCESS_TOKEN,
        "Content-Type": "application/json"  # Specify the content-type as JSON
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        #print(response.json())
        return response.json()
    elif response.status_code == 404:
        print("Error getting wiki page:", response.text)
        return None
    else:
        print(f"Failed to get Wiki page '{url}'. Status code: {response.status_code}")
        print(response.text)


def create_markdown_table(csv_file_path, headers = ["Atomic Number (Z)", "Symbol", "Atomic Mass (A)"]):
    # Initialize an empty list to store the CSV data rows
    csv_data = []
    
    # Read the CSV file
    with open(csv_file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            csv_data.append(row)
            
    # Remove "n-" from string values
    data_no_n = np.core.defchararray.replace(csv_data, 'n-', '')
    # Split values into different columns based on "_"
    data_split = np.core.defchararray.split(data_no_n, '_')
    # Convert the result into a numpy array
    data_split_array = np.array(data_split.tolist())
    # Convert the list of lists to a numpy array  
    numpy_array = data_split_array.reshape((data_split_array.shape[0], data_split_array.shape[2]))
    
    # Create a dictionary to store combined values as strings
    combined_values = {}
    
    # Loop through the array
    for row in numpy_array:
        key = row[0] # Value in the first column as the key
        symbol = row[1]
        value = row[2]  # Value in the third column
        if key in combined_values:
            combined_values[key][0] += f", [{value}]({ROOT_WIKI_SLUG}/n-{key}_{symbol}_{value})"# Add the value with a comma
        else:
            combined_values[key] = [f"[{value}]({ROOT_WIKI_SLUG}/n-{key}_{symbol}_{value})", symbol]  # Initialize with the value and value from column two
    
    # Convert the dictionary back to an array
    combined_array = np.array([[key, value[0], value[1]] for key, value in combined_values.items()])
    combined_array[:, [1, 2]] = combined_array[:, [2, 1]]
    
    markdown_table = tabulate(combined_array, tablefmt="pipe", headers=headers, numalign="left")
    data_list = [element for sublist in csv_data for element in sublist]
    
    return markdown_table, data_list

# Function to extracted child wiki page titles for a repo
def extract_child_page_titles(updated_files):
        child_page_titles = []

        endf_strings = [line for line in updated_files if line.endswith(".endf")]

        for endf_string in endf_strings:
            child_page_title = endf_string[:-5]  # Remove ".endf"
            child_page_titles.append(child_page_title)

        return child_page_titles

# Function to update nested wiki pages with job status
def update_nested_wiki_page_with_job_status(job_name_to_find='verify_endf'):
    # Get the latest pipeline for the project
    pipeline_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines"
    headers = {"PRIVATE-TOKEN": ACCESS_TOKEN, "Content-Type": "application/json"}
    response = requests.get(pipeline_url, headers=headers)

    if response.status_code != 200:
        print(f"Failed to retrieve pipelines. Status code: {response.status_code}")
        return

    pipelines = response.json()
    latest_pipeline = next((pipeline for pipeline in pipelines), None)

    if latest_pipeline:
        job_details_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines/{latest_pipeline['id']}/jobs"
        response = requests.get(job_details_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve job details. Status code: {response.status_code}")
            return

        jobs = response.json()
        target_job = next((job for job in jobs if job["name"] == job_name_to_find), None)

        if target_job:
            job_status = target_job["status"]
            job_link = f"[Job Details]({target_job['web_url']})"
            artifacts, updated_files = get_job_changes_and_artifacts(target_job['id'], latest_pipeline['id'])
            child_page_titles = extract_child_page_titles(updated_files)

            # Determine emoji based on job status
            emoji = "❓"  # Default for unknown status
            if job_status == "success":
                emoji = "👍"
            elif job_status == "failed":
                emoji = "👎"
            elif job_status == "warning":
                emoji = "⚠️"
            elif job_status in ["pending", "running", "manual", "scheduled"]:
                emoji = "⚪"

            starting_content = '## Last updated: ' + str(datetime.now())
            legend_string = '**Legend:** success = 👍, failed = 👎, warning = ⚠️, canceled = 🗙, pending = ⚪, running = ⚪, manual = ⚪, scheduled = ⚪, ❓ = Default emoji for unknown status <br><br>'
            post_datetime = str(datetime.now())
            top_content = f"{emoji} {job_name_to_find} {post_datetime} <br>Job Status: {job_link} <br>Artifacts created by this job: {artifacts if artifacts else 'No artifacts were created by this job.'} <br><br>"

            if child_page_titles is None:
                print("Child page titles not found in the job log.")
                return

            for child_page_title in child_page_titles:
                wiki_page_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{ROOT_WIKI_SLUG}%2F{child_page_title}"
                response = requests.get(wiki_page_url, headers=headers)
                existing_content = response.json().get('content')

                lines = existing_content.splitlines()
                input_string = '\n'.join(lines[1:])
                input_string = input_string.replace(legend_string, '')
                modified_string = input_string.replace("<br><br><br>", "<br><br>")

                slug = f"{ROOT_WIKI_SLUG}/{child_page_title}"
                wiki_content = top_content + modified_string
                data = {
                    "title": child_page_title,
                    "content": starting_content + "\n" + legend_string + "\n" + wiki_content,
                    "format": "markdown",
                    "slug": slug,
                    'encoding': 'UTF-8'
                }

                response = requests.put(wiki_page_url, headers=headers, json=data)
                if response.status_code == 200:
                    print(f"Wiki page {ROOT_WIKI_SLUG}/{child_page_title} updated successfully!")
                else:
                    print(f"Wiki page {ROOT_WIKI_SLUG}/{child_page_title} update failed. Status code: {response.status_code} ")

        else:
            print(f"Job '{job_name_to_find}' not found in the latest pipeline.")
    else:
        print("No pipelines found for the project.")

# Function to get job changes and artifacts
def get_job_changes_and_artifacts(job_id, pipeline_id):
    headers = {"PRIVATE-TOKEN": ACCESS_TOKEN, "Content-Type": "application/json"}

    # Get a list of artifacts for a specific job
    artifacts_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/jobs/{job_id}/artifacts"
    response = requests.get(artifacts_url, headers=headers)
    artifacts = "None"
    if response.status_code == 200:
        artifacts = artifacts_url

    # Get Pipeline Information
    pipeline_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines/{pipeline_id}"
    response = requests.get(pipeline_url, headers=headers)
    if response.status_code == 200:
        pipeline_data = response.json()
        commit_sha = pipeline_data["sha"]
    else:
        print(f"Failed to retrieve pipeline information. Status code: {response.status_code}")
        exit(1)

    # Get Pipeline Diff Information
    commit_diff_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/repository/commits/{commit_sha}/diff"
    response = requests.get(commit_diff_url, headers=headers)

    if response.status_code == 200:
        diff_data = response.json()
    else:
        print(f"Failed to retrieve commit diff. Status code: {response.status_code}")
        exit(1)

    # Create a Python list of modified files
    modified_files = []

    for diff_entry in diff_data:
        change_type = diff_entry["new_file"] and "added" or (
            diff_entry["deleted_file"] and "deleted" or "modified"
        )
        if change_type == "modified":
            modified_files.append(diff_entry["new_path"])

    print("Modified Files:")
    for file_name in modified_files:
        print(file_name)

    return artifacts, modified_files

# Function to update all nested wiki pages with all past jobs
def update_all_jobs_to_wiki(job_name_to_find='verify_endf', per_page = 15):
    # Get all pipelines for the project
    pipeline_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines"
    headers = {"PRIVATE-TOKEN": ACCESS_TOKEN, "Content-Type": "application/json"}
    
    # Get the total number of pages (first request)
    first_response = requests.get(pipeline_url, headers = headers)
    if first_response.status_code != 200:
        print(f"Failed to retrieve pipelines. Status code: {first_response.status_code}")
        return
    
    total_pages = int(first_response.headers.get('X-Total-Pages', 1))
    print("Total pages: " + str(total_pages))

    # Start the loop from the last page and work backward to page 1
    for page in range(total_pages, 0, -1):
        response = requests.get(f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines", headers={"PRIVATE-TOKEN": ACCESS_TOKEN, "Content-Type": "application/json"}, params={"page": page})

        if response.status_code != 200:
            print(f"Failed to retrieve pipelines. Status code: {response.status_code}")
            return

        pipelines = response.json()

        # Step through pipelines and update wikis
        for pipeline in pipelines:
            job_details_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/pipelines/{pipeline['id']}/jobs"
            response = requests.get(job_details_url, headers=headers)

            if response.status_code != 200:
                print(f"Failed to retrieve job details. Status code: {response.status_code}")
                return

            jobs = response.json()
            target_job = next((job for job in jobs if job["name"] == job_name_to_find), None)

            if target_job:
                job_status = target_job["status"]
                job_link = f"[Job Details]({target_job['web_url']})"
                artifacts, updated_files = get_job_changes_and_artifacts(target_job['id'], pipeline['id'])
                child_page_titles = extract_child_page_titles(updated_files)

                # Determine emoji based on job status
                emoji = "❓"  # Default for unknown status
                if job_status == "success":
                    emoji = "👍"
                elif job_status == "failed":
                    emoji = "👎"
                elif job_status == "warning":
                    emoji = "⚠️"
                elif job_status in ["pending", "running", "manual", "scheduled"]:
                    emoji = "⚪"

                starting_content = '## Last updated: ' + str(datetime.now())
                legend_string = '**Legend:** success = 👍, failed = 👎, warning = ⚠️, canceled = 🗙, pending = ⚪, running = ⚪, manual = ⚪, scheduled = ⚪, ❓ = Default emoji for unknown status <br><br>'
                _, post_datetime, _ = get_job_timestamps(target_job['id'])
                top_content = f"{emoji} {job_name_to_find} {post_datetime} <br>Job Status: {job_link} <br>Artifacts created by this job: {artifacts if artifacts else 'No artifacts were created by this job.'} <br><br>"

                if child_page_titles is None:
                    print("Child page titles not found in the job log.")
                    return

                for child_page_title in child_page_titles:
                    wiki_page_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{ROOT_WIKI_SLUG}%2F{child_page_title}"
                    response = requests.get(wiki_page_url, headers=headers)

                    # Check if existing_content is None before attempting to split it
                    existing_content = response.json().get('content')
                    if existing_content is not None:
                        #sorted_entries = fetch_and_sort_gitlab_wiki(existing_content)
                        lines = existing_content.splitlines()
                        input_string = '\n'.join(lines[1:])
                        input_string = input_string.replace(legend_string, '')
                        modified_string = input_string.replace("<br><br><br>", "<br><br>")

                    else:
                        print("No existing content found for the wiki page.")
                        modified_string = "None"

                    slug = f"{ROOT_WIKI_SLUG}/{child_page_title}"
                    wiki_content = top_content + modified_string
                    data = {
                        "title": child_page_title,
                        "content": starting_content + "\n" + legend_string + "\n" + wiki_content,
                        "format": "markdown",
                        "slug": slug,
                        'encoding': 'UTF-8'
                    }

                    response = requests.put(wiki_page_url, headers=headers, json=data)
                    if response.status_code == 200:
                        print(f"Wiki page {ROOT_WIKI_SLUG}/{child_page_title} updated successfully!")
                    else:
                        print(f"Wiki page {ROOT_WIKI_SLUG}/{child_page_title} update failed. Status code: {response.status_code} ")
            else:
                print(f"Job '{job_name_to_find}' not found in the latest pipeline: {pipeline}")

# Function to get date and time info from a GitLab job
def get_job_timestamps(job_id):
    # Get job details by job ID
    job_url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/jobs/{job_id}"
    headers = {"PRIVATE-TOKEN": ACCESS_TOKEN, "Content-Type": "application/json"}
    response = requests.get(job_url, headers=headers)

    if response.status_code == 200:
        job_details = response.json()
        created_at = job_details.get("created_at")
        started_at = job_details.get("started_at")
        finished_at = job_details.get("finished_at")

        # Convert timestamps to datetime objects for further processing
        created_at_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%fZ") if created_at else "None"
        started_at_dt = datetime.strptime(started_at, "%Y-%m-%dT%H:%M:%S.%fZ") if started_at else "None"
        finished_at_dt = datetime.strptime(finished_at, "%Y-%m-%dT%H:%M:%S.%fZ") if finished_at else "None"

        return (created_at_dt, started_at_dt, finished_at_dt)
    else:
        print(f"Failed to retrieve job details. Status code: {response.status_code}")
        return "None", "None", "None"

# Function to sort wiki entries by datetime
def fetch_and_sort_gitlab_wiki(wiki_data):
    # Split the data into individual entries
    entries = wiki_data.split("<br><br>")[:-1]
    
    # Create a list of tuples containing (emoji, entry, datetime) for sorting
    entry_datetime_list = []
    for entry in entries:
        emoji = entry.split(" ")[0].strip()
        timestamp_str = entry.split(' ')[2].strip()
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            entry_datetime_list.append((emoji, entry, timestamp))
        except:
            pass

    # Sort the list by datetime
    sorted_entries = [entry for _, entry, _ in sorted(entry_datetime_list, key=lambda x: x[2])]
    
    # Combine the sorted entries into a string
    sorted_data = "\n".join(sorted_entries)
    
    # Include the header back at the top
    finished_data = f"## Last updated: {str(datetime.now())}\n**Legend:** success = 👍, failed = 👎, warning = ⚠️, canceled = 🗙, pending = ⚪, running = ⚪, manual = ⚪, scheduled = ⚪, ❓ = Default emoji for unknown status <br><br>\n{sorted_data}"
    
    return finished_data

if __name__ == "__main__":
    # Get the current working directory
    current_directory = os.getcwd()
    # Print the current working directory
    print("Current Working Directory: ", current_directory)
    
    # Create nested wiki pages
    #main_wiki_content, data_list = create_markdown_table(CSV_FILE_PATH)
    #for page in data_list:
    #    create_or_update_nested_wiki_page(page, "None", root_wiki = False)

    # Call the function to update all past jobs to the appropriate wiki sub-pages
    #update_all_jobs_to_wiki()

    # Get the content of a specific wiki page
    get_wiki_page_content(ROOT_WIKI_SLUG)

    # Update nested wiki pages with job status
    update_nested_wiki_page_with_job_status(job_name_to_find="verify_endf")
