import requests
import base64
import json
from dotenv import load_dotenv
import os
import time
load_dotenv()
 
# ========================
#  CONFIGURATION
# ========================
 
JIRA_URL = os.getenv("JIRA_BASE_URL", "https://lilly-jira.atlassian.net")
JIRA_USERNAME = os.getenv("EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")
PROJECT_KEY = "DEMOBASIC"
 
CLIENT_ID = os.getenv("CLIENT_ID", "xray-cloud-client-id")
CLIENT_SECRET = os.getenv("ClIENT_SECRET", "xray-cloud-client-secret")
XRAY_URL = os.getenv("XRAY_BASE_URL", "https://xray.cloud.getxray.app/api/v2")
 
AUTH = base64.b64encode(f"{JIRA_USERNAME}:{API_TOKEN}".encode()).decode()
 
 
# =====================================
#  Get Xray OAuth Token
# =====================================
 
def get_oauth_token():
    url = f"{XRAY_URL}/authenticate"
    payload = {"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET}
    r = requests.post(url, json=payload)
    r.raise_for_status()
    return r.text.strip('"')
 
 
# =====================================
#  Create Jira Issue (Test or Execution)
# =====================================
 
def create_issue(summary, issue_type):
    url = f"{JIRA_URL}/rest/api/3/issue"
    headers = {
        "Authorization": f"Basic {AUTH}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {"type": "paragraph", "content": [{"type": "text", "text": summary}]}
                ]
            }
        }
    }
    r = requests.post(url, headers=headers, json=payload)
    r.raise_for_status()
    # print("Create Issue Response:", r.json(),end="\n\n")
    return r.json()
 
 
# =====================================
#  Get Internal Issue ID
# =====================================
 
def get_internal_issue_id(issue_key):
    url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}?fields=id"
    headers = {"Authorization": f"Basic {AUTH}", "Accept": "application/json"}
    r = requests.get(url, headers=headers)
    # print("get_internal_issue_id response", r.json(),end="\n\n")
    r.raise_for_status()
    return r.json()["id"]
 
 
# =====================================
#  Add Test Steps
# =====================================
 
def add_jira_test_steps(token, issue_id, steps):
    url = f"{XRAY_URL}/graphql"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    query = """
        mutation($issueId: String!, $step: CreateStepInput!) {
          addTestStep(issueId: $issueId, step: $step) {
            id
            action
            result
          }
        }
    """
    for i, step in enumerate(steps, 1):
        step_dict = step.dict()
        variables = {
            "issueId": issue_id,
            "step": {
                "action": step_dict['action'],
                "data": step_dict['data'],
                "result": step_dict['expected_result'],
            }
        }

        # Retry logic to handle eventual consistency / indexing delays in Xray/Jira
        max_retries = 5
        for attempt in range(1, max_retries + 1):
            r = requests.post(url, headers=headers, json={"query": query, "variables": variables})
            try:
                data = r.json()
            except Exception:
                data = {"errors": [{"message": f"Invalid JSON response (status {r.status_code})"}]}

            if "errors" in data:
                # If the error indicates the test was not found, wait and retry
                msgs = " ".join(err.get('message', '') for err in data['errors'])
                if "not found" in msgs.lower() and attempt < max_retries:
                    wait = 1 * attempt
                    print(f" GraphQL error on step {i} (attempt {attempt}/{max_retries}): {msgs}. Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                else:
                    print(f" GraphQL error on step {i}: {data['errors']}")
                    break
            else:
                print(f" Added step {i}: {step_dict['action']}")
                break
 
 
# =====================================
#  Link Test to Execution
# =====================================
 
def link_test_to_execution(token, exec_id, test_id):
    query = """
        mutation($issueId: String!, $testIssueIds: [String!]!) {
          addTestsToTestExecution(issueId: $issueId, testIssueIds: $testIssueIds) {
            addedTests
            warning
          }
        }
    """
    url = f"{XRAY_URL}/graphql"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    variables = {"issueId": exec_id, "testIssueIds": [test_id]}
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        r = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        try:
            data = r.json()
        except Exception:
            data = {"errors": [{"message": f"Invalid JSON response (status {r.status_code})"}]}

        print("link_test_to_execution data response:", data, end="\n\n")
        if "errors" in data:
            msgs = " ".join(err.get('message', '') for err in data['errors'])
            if "not found" in msgs.lower() and attempt < max_retries:
                wait = 1 * attempt
                print(f" Error linking test (attempt {attempt}/{max_retries}): {msgs}. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f" Error linking test: {data['errors']}")
                break
        else:
            print(f" Linked test {test_id} to execution {exec_id}")
            break
 
 
# =====================================
#  Get Test Run ID
# =====================================
 
def get_test_run_id(token, exec_id, test_id):
    query = """
        query($testExecIssueId: String!, $testIssueId: String!) {
          getTestRun(testExecIssueId: $testExecIssueId, testIssueId: $testIssueId) {
            id
          }
        }
    """
    url = f"{XRAY_URL}/graphql"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    variables = {"testExecIssueId": exec_id, "testIssueId": test_id}
    max_retries = 6
    for attempt in range(1, max_retries + 1):
        r = requests.post(url, headers=headers, json={"query": query, "variables": variables})
        try:
            data = r.json()
        except Exception:
            data = {"errors": [{"message": f"Invalid JSON response (status {r.status_code})"}]}

        print("get_test_run_id data response:", data, end="\n\n")
        if "errors" in data or not data.get("data", {}).get("getTestRun"):
            msgs = ''
            if "errors" in data:
                msgs = " ".join(err.get('message', '') for err in data['errors'])
            if attempt < max_retries:
                wait = 1 * attempt
                print(f" Could not fetch test run (attempt {attempt}/{max_retries}): {msgs or data}. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            print(f" Could not fetch test run: {data}")
            return None
        return data["data"]["getTestRun"]["id"]
 
 
# =====================================
#  Update Test Result
# =====================================
 
def update_test_result(token, run_id, status="PASSED"):
    query = """
        mutation($testRunId: String!, $status: String!) {
          updateTestRunStatus(id: $testRunId, status: $status)
        }
    """
    url = f"{XRAY_URL}/graphql"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    variables = {"testRunId": run_id, "status": status}
    r = requests.post(url, headers=headers, json={"query": query, "variables": variables})
    if not r.ok:
        print(f" Error updating test result: {r.status_code} - {r.text}")
    else:
        print(f" Updated test run {run_id} - {status}")
 
 
# =====================================
#  MAIN FLOW
# =====================================
 
# if __name__ == "__main__":
#     xray_token = get_oauth_token()
#     print(" Xray token obtained.")
 
#     # Create Test
#     test_issue = create_issue("Automated Login Test", "Test")
#     test_key = test_issue["key"]
#     test_id = get_internal_issue_id(test_key)
#     print(f" Created Test issue: {test_key} (id={test_id})")
 
#     # Add Steps
#     steps = [
#         {"action": "Open login page", "data": "Go to https://app.example.com/login", "result": "Login page loads"},
#         {"action": "Enter credentials", "data": "username=test, password=pass", "result": "User logged in"},
#         {"action": "Verify dashboard", "data": "", "result": "Dashboard visible"}
#     ]
#     add_jira_test_steps(xray_token, test_id, steps)
 
#     # Create Execution
#     exec_issue = create_issue("Execution - Automated Login Test", "Test Execution")
#     exec_key = exec_issue["key"]
#     exec_id = get_internal_issue_id(exec_key)
#     print(f" Created Test Execution: {exec_key} (id={exec_id})")
 
#     # Link test and update result
#     link_test_to_execution(xray_token, exec_id, test_id)
#     run_id = get_test_run_id(xray_token, exec_id, test_id)
#     if run_id:
#         update_test_result(xray_token, run_id, "TODO")
 
#     print(" All done successfully!")
