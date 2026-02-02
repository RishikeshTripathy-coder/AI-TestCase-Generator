import requests
from requests.auth import HTTPBasicAuth
import json
import os
from dotenv import load_dotenv
load_dotenv()

email = os.getenv("EMAIL")
api_token= os.getenv("JIRA_API_TOKEN")
# Replace these with your Jira details
JIRA_DOMAIN = "https://lilly-jira.atlassian.net"
ISSUE_KEY = "SAS2R-87"
EMAIL = email
API_TOKEN = api_token
url = f"{JIRA_DOMAIN}/rest/api/2/issue/{ISSUE_KEY}"
auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {
    "Accept": "application/json"
}
response = requests.get(url, headers=headers, auth=auth)
issue = response.json()
print(json.dumps(issue, indent=4))
# Get the description
description = issue['fields'].get('description', 'No description found.')
# Try to get acceptance criteria from custom field or description
acceptance_criteria = None
# If your team uses a custom field for acceptance criteria, replace 'customfield_XXXXX' with the actual field ID
acceptance_criteria = issue['fields'].get('customfield_XXXXX')
# If not, try to extract from description (if labeled)
if not acceptance_criteria and description:
    import re
    match = re.search(r'(Acceptance Criteria|AC|Definition of Done)[:\n-]*([\s\S]+)', description, re.IGNORECASE)
    if match:
        acceptance_criteria = match.group(2).strip()
print("Description:\n", description)
print("\nAcceptance Criteria:\n", acceptance_criteria or "Not found.")