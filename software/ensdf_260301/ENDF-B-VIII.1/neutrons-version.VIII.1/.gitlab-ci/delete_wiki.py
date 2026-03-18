# -*- coding: utf-8 -*-
"""
Created on Tue Jul 25 13:27:14 2023

@author: rcoles
"""

import requests
import yaml
import json
import os
from urllib.parse import quote

# Define Constants
GITLAB_URL = "https://git.nndc.bnl.gov"
PROJECT_ID = "27"
ROOT_WIKI_SLUG = "Neutron-Artifacts"
ACCESS_TOKEN = os.environ.get('WIKI_ACCESS_TOKEN')
CSV_FILE_PATH = "/builds/endf/library/neutrons/.gitlab-ci/neutrons.csv"

# Function to get all wiki pages
def get_wiki_pages():
    url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis"
    headers = {
        "PRIVATE-TOKEN": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        wiki_pages = json.loads(response.text)
        print('Current wiki pages:\n')
        print(yaml.dump(wiki_pages, allow_unicode=True, default_flow_style=False))
        return wiki_pages
    else:
        print(f"Failed to get wiki pages. Status code: {response.status_code}")
        return None

# Function to delete wiki pages
def delete_wiki_pages(pages_to_delete):
    headers = {
        "PRIVATE-TOKEN": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }

    for page in pages_to_delete:
        slug = f"{ROOT_WIKI_SLUG}/{page}"
        slug_encoded = quote(slug, safe='')
        url = f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{slug_encoded}"
        response = requests.delete(url, headers=headers)
        print(f'Deleting: {url}')
        if response.status_code == 204:
            print(f"Successfully deleted wiki page: {slug}")
        else:
            print(f"Failed to delete wiki page: {slug}. Status code: {response.status_code}")

def delete_all_wiki_pages(wiki_pages):
    # Headers for the requests
    headers = {
        "PRIVATE-TOKEN": ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    for page in wiki_pages:
        if isinstance(page, dict):
            slug = page['slug']
        elif isinstance(page, list):
            slug = ROOT_WIKI_SLUG + '/' + page
        else:
            return "The wiki pages variable is neither a dictionary nor a list."
        slug = page['slug']
        slug_encoded = quote(slug, safe='')
        response = requests.delete(f"{GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{slug_encoded}", headers=headers)
        print(f'Deleteing : {GITLAB_URL}/api/v4/projects/{PROJECT_ID}/wikis/{slug}')
        if response.status_code == 204:
            print(f"Successfully deleted wiki page: {slug}")
        else:
            print(f"Failed to delete wiki page: {slug}. Status code: {response.status_code}")

if __name__ == "__main__":
    # Get a list of all wiki pages for the project
    wiki_pages = get_wiki_pages()

    # Delete wiki pages (uncomment the line below if you want to delete specific pages)
    # delete_wiki_pages(["PageToDelete", "AnotherPageToDelete"])

    # Delete all wiki pages
    delete_all_wiki_pages(wiki_pages)
