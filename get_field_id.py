import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
load_dotenv()

JIRA_DOMAIN = os.getenv("JIRA_BASE_URL")
EMAIL = os.getenv("EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

url = f"{JIRA_DOMAIN}/rest/api/3/field"
auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = { "Accept": "application/json" }

response = requests.get(url, headers=headers, auth=auth)
fields = response.json()

for field in fields:
    if "acceptance" in field["name"].lower():
        print(f"{field['name']} -> {field['id']}")
