import requests
from fastapi import HTTPException
from requests.auth import HTTPBasicAuth
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
load_dotenv()

class JiraStory(BaseModel):
    key: str
    summary: str
    description: Optional[str]
    acceptance_criteria: Optional[str]

email = os.getenv("EMAIL")
api_token=os.getenv("JIRA_API_TOKEN")
# Replace these with your Jira details
JIRA_DOMAIN = "https://lilly-jira.atlassian.net"
EMAIL = email
API_TOKEN = api_token
PROJECT_KEY = "SAS2R"
ACCEPTANCE_CRITERIA_FIELD_ID=os.getenv("ACCEPTANCE_CRITERIA_FIELD_ID")

def extract_text_from_rich_text(field_data: dict) -> str:
    """Extracts plain text from Jira rich text (ADF - Atlassian Document Format)."""
    if not field_data or not isinstance(field_data, dict):
        return ""
    
    texts = []

    def recurse(content):
        for item in content:
            if item.get("type") == "text":
                texts.append(item.get("text", ""))
            elif "content" in item:
                recurse(item["content"])

    if "content" in field_data:
        recurse(field_data["content"])
    
    return " ".join(texts)

# jql = f'project={PROJECT_KEY} AND issuetype=Story'
jql = f'project={PROJECT_KEY} AND issuetype=Story AND status = Approved ORDER BY created DESC'
# "project = SAS2R AND type = Story AND status = Approved ORDER BY created DESC"
url = f"{JIRA_DOMAIN}/rest/api/3/search/jql"

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {
    "Accept": "application/json"
}

params = {
        "jql": jql,
        "fields": "summary,key,description,customfield_10121",
        "maxResults": 100
    }

response = requests.get(url, headers=headers, params=params, auth=auth)
if response.status_code != 200:
    raise HTTPException(status_code=500, detail="Failed to fetch Jira stories")

issues = response.json().get('issues', [])
stories = []

for issue in issues:
    fields = issue.get("fields", {})
    key= issue.get("key")
    summary= fields.get("summary")
    description_raw = fields.get("description")
    description = description_raw['content'][0]['content'][0]['text']
    acceptance_raw = fields.get(ACCEPTANCE_CRITERIA_FIELD_ID)
    print(key, summary, description, acceptance_raw)

    

# issues = response.json().get('issues', [])

# for issue in issues:
#     print(json.dumps(issue['fields']['description']['content'], indent=4))
#     # print(f"{issue['key']}: {issue['fields']['summary']}")