
# GitLab Wiki Management Scripts

This repository contains a collection of Python scripts to manage GitLab Wiki pages. Each script has a specific function related to backing up, restoring, deleting, and interacting with the Wiki via the GitLab API.

## Scripts

### 1. `backup_wiki.py`

#### Description:
- This script backs up all the pages of a GitLab Wiki into a separate branch in the same repository.

#### Usage:
- Set the environment variables `WIKI_ACCESS_TOKEN`, `CI_PROJECT_ID`, and `CI_PROJECT_NAME`.
- Run the script.

```bash
python backup_wiki.py
```

### 2. `delete_wiki.py`

#### Description:
- This script deletes Wiki pages based on specified criteria.

#### Usage:
- Set the environment variable `WIKI_ACCESS_TOKEN`.
- Update the `PROJECT_ID` and `ROOT_WIKI_SLUG` as per your project's details.
- Run the script.

```bash
python delete_wiki.py
```

### 3. `git-api-wiki.py`

#### Description:
- This script interacts with the GitLab API to perform various operations on a Wiki.

#### Usage:
- Set the environment variable `WIKI_ACCESS_TOKEN`.
- Update the `PROJECT_ID` and `ROOT_WIKI_SLUG` as per your project's details.
- Run the script.

```bash
python git-api-wiki.py
```

### 4. `restore_wiki.py`

#### Description:
- This script restores a GitLab Wiki from a backup stored in a separate branch.

#### Usage:
- Set the environment variables `WIKI_ACCESS_TOKEN`, `CI_PROJECT_ID`, and `CI_PROJECT_NAME`.
- Run the script.

```bash
python restore_wiki.py
```

## Dependencies

- Python 3.x
- `requests` library

## Installation

```bash
pip install requests
```

## Author

- Script Author: rcoles

For more information, please refer to the individual scripts.
