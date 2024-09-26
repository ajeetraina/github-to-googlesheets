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
