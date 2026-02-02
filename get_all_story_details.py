import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv
load_dotenv()

def extract_text_from_adf(adf: dict) -> str:
    """
    Extract plain text from Jira's ADF (Atlassian Document Format) rich text content.
    Handles paragraphs, lists, and nested structures.
    """
    if not adf or not isinstance(adf, dict):
        return ""

    lines = []

    def walk(content, indent=""):
        if not content:
            return

        for node in content:
            node_type = node.get("type")
            node_content = node.get("content", [])

            # Handle text node
            if node_type == "text":
                lines.append(indent + node.get("text", ""))

            # Handle paragraphs
            elif node_type == "paragraph":
                walk(node_content, indent)

            # Handle bullet or ordered lists
            elif node_type in ("bulletList", "orderedList"):
                for index, item in enumerate(node_content, start=1):
                    prefix = "-" if node_type == "bulletList" else f"{index}."
                    walk(item.get("content", []), indent + prefix + " ")

            # Handle list item
            elif node_type == "listItem":
                walk(node_content, indent)

            # Other nodes (tables, etc.) can be added here as needed
            else:
                walk(node_content, indent)

    walk(adf.get("content", []))
    return "\n".join(lines).strip()


# JIRA_URL = "https://lilly-jira.atlassian.net"
# API_ENDPOINT = f"{JIRA_URL}/rest/api/3/search/jql"
# USERNAME = os.getenv("EMAIL")
# API_TOKEN = os.getenv("JIRA_API_TOKEN")

# # JQL to get all stories
# jql = "project=SAS2R AND issuetype=Story AND status = Approved ORDER BY created DESC"

# # Fields to fetch: key, summary, description, acceptance criteria
# fields = ["key", "summary", "description", "customfield_10121"]  # Replace with your actual custom field ID for Acceptance Criteria

# params = {
#     "jql": jql,
#     "fields": ",".join(fields),
#     "maxResults": 100  # Adjust as needed (max 1000 per request)
# }

# response = requests.get(
#     API_ENDPOINT,
#     params=params,
#     auth=HTTPBasicAuth(USERNAME, API_TOKEN),
#     headers={"Accept": "application/json"}
# )

# if response.status_code == 200:
#     issues = response.json()["issues"]
#     for issue in issues:
#         key = issue["key"]
#         summary = issue["fields"]["summary"]
#         print(f"key {key}, summary {summary}")
#         # description = extract_text_from_adf(issue["fields"].get("description", ""))
#         # acceptance_criteria = extract_text_from_adf(issue["fields"].get("customfield_10121", ""))
#         # print(f"\nDescription: {description}\nAcceptance Criteria: {acceptance_criteria}\n")
# else:
#     print("Failed to fetch issues:", response.status_code, response.text)