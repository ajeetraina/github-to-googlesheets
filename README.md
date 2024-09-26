# github-to-googlesheets


## Table of Contents

1. Enable the Google Sheets API
2. Create Service Account Credentials
3. Rename the JSON file
4. Update the Python Script
5. Set up GitHub API
6. Set up Google Sheets API
7.  Create a Google Sheet
8.  Run the Script

## Step 1: Enable the Google Sheets API:

- Go to the Google Cloud Console.
- Create a new project or select an existing one.
- Navigate to APIs & Services > Library.
- Search for and enable the Google Sheets API and Google Drive API.

## Step 2. Create Service Account Credentials:

- Go to APIs & Services > Credentials.
- Click on Create Credentials, and select Service Account.
- Fill in the necessary details and create a service account.
Once created, navigate to the service account, and click Add Key > - Create New Key.
- Select JSON as the key type and download the JSON file.


## Step 3. Rename the JSON file:

- Move the downloaded JSON file to your project directory (where fetch.py is located).
- Rename the file to something like google_creds.json (or any name you'd prefer).

## Step 4. Update the script:

- Modify the file path in your Python script to match the new credentials file:

```
GOOGLE_CREDS = ServiceAccountCredentials.from_json_keyfile_name('google_creds.json', SCOPES)
```

## Step 5. Set up GitHub API

Replace 'your_github_token' with your GitHub token (personal access token with necessary scopes).

## Step 6. Set up Google Sheets API:

- Replace 'your_google_creds.json' with the path to your Google credentials file. Set up Google Sheets API following this guide.

## Step 7. Create a Google Sheet 

You will need to create a Google Sheet and share it with the email from your Google credentials file.


## Step 8. Run the Script

```
python3 fetch_repo.py
```

This script will fetch all repositories in the dockersamples organization, calculate their age, and check if they are archived, who created them, and if they have a LICENSE and CONTRIBUTING.md file.
It will then append this information to a Google Sheet.


```
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# GitHub API setup
ORG_NAME = 'dockersamples'
GITHUB_TOKEN = 'github_pat_XXXXX'  # Replace with your GitHub Token
GITHUB_API_URL = f'https://api.github.com/orgs/{ORG_NAME}/repos'

# Google Sheets API setup
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDS = ServiceAccountCredentials.from_json_keyfile_name('dockersamples.json', SCOPES)
client = gspread.authorize(GOOGLE_CREDS)
sheet = client.open_by_key('1w_GVXXXXQs').sheet1  # Replace with your Google Sheet

def fetch_github_repos():
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    response = requests.get(GITHUB_API_URL, headers=headers)
    return response.json()

def populate_sheet(repos):
    sheet.append_row(["Repo Name", "Age (Years)", "Archived", "Creator", "LICENSE", "CONTRIBUTING.md"])
    for repo in repos:
        repo_name = repo['name']
        created_at = repo['created_at']
        archived = repo['archived']
        creator = repo['owner']['login']
        license_exists = 'LICENSE' in [file['name'] for file in requests.get(repo['contents_url'].replace('{+path}', ''), headers={'Authorization': f'token {GITHUB_TOKEN}'}).json()]
        contributing_exists = 'CONTRIBUTING.md' in [file['name'] for file in requests.get(repo['contents_url'].replace('{+path}', ''), headers={'Authorization': f'token {GITHUB_TOKEN}'}).json()]

        age_years = (datetime.now() - datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")).days // 365

        sheet.append_row([repo_name, age_years, archived, creator, license_exists, contributing_exists])

repos = fetch_github_repos()
populate_sheet(repos)
```



Result:

```
Repo Name	Age (Years)	Archived	Creator	LICENSE	CONTRIBUTING.md
example-voting-app	8	FALSE	dockersamples	TRUE	FALSE
docker-swarm-visualizer	8	FALSE	dockersamples	TRUE	FALSE
atsea-sample-shop-app	7	TRUE	dockersamples	TRUE	FALSE
..
..
```

If your script is only fetching a subset of repositories, this is likely because GitHub's API paginates results, with a default limit of 30 items per page. You'll need to add pagination to your script to fetch all repositories.

### Pagination Handling:

   - The while True loop keeps fetching repositories page by page until it encounters an empty page.
   - per_page=100 fetches up to 100 repositories per request (maximum allowed by GitHub).
  - It increments the page parameter to get the next set of repositories.
### Appending Data:

  The repos list collects all repositories from multiple pages.

Be aware of the quota and API limit. If you encounter the following error, we have a workaround for you

```
gspread.exceptions.APIError: APIError: [429]: Quota exceeded for quota metric 'Write requests' and limit 'Write requests per minute per user' of service 'sheets.googleapis.com' for consumer 'project_number:1037915935586'.
```

The error you encountered indicates that you have exceeded the quota for write requests to the Google Sheets API. Google imposes a limit on the number of requests you can make per minute, which includes both reading from and writing to spreadsheets.

```
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# GitHub API setup
ORG_NAME = 'dockersamples'
GITHUB_TOKEN = 'github_pat_11AACXXXXXSVqbqenmC1dAscc55HhAmheRn7DOMZX4XSXdraFo1W'  # Replace with your GitHub Token
GITHUB_API_URL = f'https://api.github.com/orgs/{ORG_NAME}/repos'
PER_PAGE = 100  # Max items per page

# Google Sheets API setup
SCOPES = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE_CREDS = ServiceAccountCredentials.from_json_keyfile_name('dockersamples.json', SCOPES)
client = gspread.authorize(GOOGLE_CREDS)
sheet = client.open_by_key('1w_GVnnaOPdfPVuPA7XXXKQs').sheet1  # Replace with your Google Sheet

def fetch_github_repos():
    headers = {'Authorization': f'token {GITHUB_TOKEN}'}
    repos = []
    page = 1

    while True:
        logging.info(f"Fetching page {page}...")
        response = requests.get(GITHUB_API_URL, headers=headers, params={'per_page': PER_PAGE, 'page': page})
        data = response.json()

        if response.status_code != 200:
            logging.error(f"Error fetching repositories: {data.get('message')}")
            break

        if not data:
            logging.info("No more repositories to fetch.")
            break  # Exit loop if no more data

        logging.info(f"Found {len(data)} repositories on page {page}.")
        repos.extend(data)
        page += 1  # Move to the next page

    logging.info(f"Total repositories fetched: {len(repos)}")
    return repos

def populate_sheet(repos):
    rows_to_add = [["Repo Name", "Age (Years)", "Archived", "Creator", "LICENSE", "CONTRIBUTING.md"]]

    for repo in repos:
        repo_name = repo['name']
        created_at = repo['created_at']
        archived = repo['archived']
        creator = repo['owner']['login']

        # Check for LICENSE and CONTRIBUTING.md in the repo's contents
        contents_url = repo['contents_url'].replace('{+path}', '')
        logging.info(f"Checking contents for repository: {repo_name}...")
        content_response = requests.get(contents_url, headers={'Authorization': f'token {GITHUB_TOKEN}'}).json()

        license_exists = any(file['name'] == 'LICENSE' for file in content_response)
        contributing_exists = any(file['name'] == 'CONTRIBUTING.md' for file in content_response)

        # Calculate age of the repository
        age_years = (datetime.now() - datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")).days // 365

        # Collect data for batch write
        rows_to_add.append([repo_name, age_years, archived, creator, license_exists, contributing_exists])
        logging.info(f"Added {repo_name} to rows.")

        time.sleep(0.5)  # Optional: add a small delay to avoid hitting the API limits

    # Write all collected rows to the sheet at once
    logging.info("Writing data to Google Sheets...")
    sheet.insert_rows(rows_to_add, 1)  # Insert starting from the first row
    logging.info("Data written successfully.")

repos = fetch_github_repos()
populate_sheet(repos)
```

Result:

```
2024-09-26 20:07:31,238 - INFO - Added scout-demo-service to rows.
2024-09-26 20:07:31,740 - INFO - Checking contents for repository: wearedevelopers-2023...
2024-09-26 20:07:32,189 - INFO - Added wearedevelopers-2023 to rows.
2024-09-26 20:07:32,694 - INFO - Checking contents for repository: face-detection-tensorjs...
2024-09-26 20:07:33,171 - INFO - Added face-detection-tensorjs to rows.
2024-09-26 20:07:33,675 - INFO - Checking contents for repository: scout-demo-voting-app...
2024-09-26 20:07:34,056 - INFO - Added scout-demo-voting-app to rows.
2024-09-26 20:07:34,557 - INFO - Checking contents for repository: extensions-demo...
2024-09-26 20:07:35,136 - INFO - Added extensions-demo to rows.
2024-09-26 20:07:35,641 - INFO - Checking contents for repository: compose-demos...
2024-09-26 20:07:36,057 - INFO - Added compose-demos to rows.
2024-09-26 20:07:36,562 - INFO - Checking contents for repository: blog-react-app...
2024-09-26 20:07:36,962 - INFO - Added blog-react-app to rows.
2024-09-26 20:07:37,467 - INFO - Checking contents for repository: todo-list...
2024-09-26 20:07:38,034 - INFO - Added todo-list to rows.
2024-09-26 20:07:38,541 - INFO - Checking contents for repository: genai-chatbot...
2024-09-26 20:07:39,009 - INFO - Added genai-chatbot to rows.
2024-09-26 20:07:39,513 - INFO - Checking contents for repository: todo-list-app...
2024-09-26 20:07:40,040 - INFO - Added todo-list-app to rows.
2024-09-26 20:07:40,544 - INFO - Checking contents for repository: python-flask-redis...
2024-09-26 20:07:41,016 - INFO - Added python-flask-redis to rows.
2024-09-26 20:07:41,524 - INFO - Checking contents for repository: build-cloud-cookbook...
2024-09-26 20:07:42,106 - INFO - Added build-cloud-cookbook to rows.
2024-09-26 20:07:42,610 - INFO - Checking contents for repository: nginx-node-redis...
2024-09-26 20:07:43,022 - INFO - Added nginx-node-redis to rows.
2024-09-26 20:07:43,523 - INFO - Checking contents for repository: scout-metrics-exporter...
2024-09-26 20:07:43,998 - INFO - Added scout-metrics-exporter to rows.
2024-09-26 20:07:44,500 - INFO - Checking contents for repository: CodeExplorer...
2024-09-26 20:07:45,072 - INFO - Added CodeExplorer to
```
