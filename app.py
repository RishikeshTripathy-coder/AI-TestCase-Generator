import os
import json
import re
import yaml
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import fitz  # PyMuPDF
from docx import Document
from light_client import LIGHTClient

# --- ENVIRONMENT VARIABLES ---
YOUR_USER = os.getenv("EMAIL")
USER = os.getenv("USER", "").lower()

if not YOUR_USER or not USER:
    raise EnvironmentError("EMAIL and USER environment variables must be set.")

client = LIGHTClient()
CORTEX_BASE = "https://api.cortex.lilly.com"
GENERATOR_MODEL_NAME = f"{USER}-gherkin-generator-model"

# --- CONSTANTS ---
ENGLISH_WORDS = {
    "this", "is", "a", "valid", "project", "requirement", "complete", "finish", "task",
    "document", "user", "email", "data", "analysis", "code", "design", "plan", "test",
    "review", "create", "update", "implement", "run", "execute", "process", "system",
    "shall", "provide", "information", "on", "the", "help", "page", "if", "you", "are",
    "facing", "an", "issue", "please", "contact", "or", "so", "that", "can", "get",
    "assistance", "when", "have", "questions", "and", "needs", "access", "for", "business",
    "purposes", "feature", "relates", "to", "local", "onboarding", "of", "affiliate",
    "approved", "core", "story", "as", "per", "system", "security", "admin", "sop"
}

# --- HELPER FUNCTIONS ---

def to_adf_format(text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
    }

def is_valid_requirement(req: str) -> bool:
    if not req or len(req.strip().split()) < 3 or not re.search(r"[a-zA-Z]", req):
        return False
    words = [w.lower() for w in req.split() if re.match(r"^[a-zA-Z]+$", w)]
    ratio = len([w for w in words if w in ENGLISH_WORDS]) / len(words) if words else 0
    return ratio >= 0.3

def clean_model_output(raw_output: str) -> str:
    cleaned = re.sub(r"```json|```", "", raw_output.strip(), flags=re.IGNORECASE)
    match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
    return match.group(1) if match else cleaned

def call_model(model_name: str, prompt: str) -> str:
    url = f"{CORTEX_BASE}/model/ask/{model_name}"
    response = client.post(url, data={"q": prompt}, headers={"Content-Type": "application/x-www-form-urlencoded"})
    response.raise_for_status()
    return response.json().get("message", "").strip()

def extract_text_from_pdf(file):
    try:
        file.seek(0)
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            return "".join([page.get_text() for page in doc])
    except Exception as e:
        print(f"Failed to extract PDF text: {e}")
        return ""

def extract_text_from_docx(file):
    try:
        file.seek(0)
        return "\n".join([p.text for p in Document(file).paragraphs])
    except Exception as e:
        print(f"Failed to extract DOCX text: {e}")
        return ""

def extract_text_from_adf(desc):
    def parse(node):
        if isinstance(node, str):
            return node
        elif isinstance(node, dict):
            node_type = node.get("type", "")
            if node_type == "paragraph":
                return " ".join(child.get("text", "") for child in node.get("content", [])) + "\n"
            return "".join(parse(child) for child in node.get("content", []))
        return ""
    return parse(desc).strip()

def rubric_score(cases_list):
    score = 5
    if not cases_list or len(cases_list) < 2:
        score -= 1
    titles = [c["Title"].strip().lower() for c in cases_list]
    if len(set(titles)) != len(titles):
        score -= 1
    for case in cases_list:
        steps = case.get("Test Steps", "")
        if not steps or len(steps.strip()) < 20:
            score -= 1
            break
    return max(score, 1)

def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())

def remove_duplicates(new_cases, existing_titles_set):
    unique = []
    for case in new_cases:
        t = case.get("Title", "").strip().lower()
        if t and t not in existing_titles_set:
            existing_titles_set.add(t)
            unique.append(case)
    return unique

# --- JIRA INTEGRATION ---

def fetch_jira_issues(jira_base, jql, token):
    url = f"{jira_base}/rest/api/3/search/jql"
    response = requests.get(url, headers={"Accept": "application/json"}, params={"jql": jql}, auth=HTTPBasicAuth(YOUR_USER, token))
    if response.status_code != 200:
        raise Exception(f"Jira error: {response.status_code} - {response.text}")
    return response.json().get("issues", [])

def create_jira_issue(jira_base, token, project_key, summary, description, priority, issue_type="Test", parent_issue_key=None):
    url = f"{jira_base}/rest/api/3/issue"
    issue_data = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": to_adf_format(description),
            "issuetype": {"name": issue_type},
            "priority": {"name": priority}
        }
    }
    response = requests.post(url, headers={"Content-Type": "application/json"}, json=issue_data, auth=HTTPBasicAuth(YOUR_USER, token))
    if response.status_code != 201:
        print(f"Failed to create Jira issue: {response.status_code} - {response.text}")
        return None
    return response.json().get("key")

def add_test_step(jira_base, token, issue_key, steps):
    url = f"{jira_base}/rest/raven/1.0/api/test/{issue_key}/step"
    payload = [{"index": i, "action": s["Action"], "result": s["ExpectedResult"]} for i, s in enumerate(steps)]
    response = requests.put(url, headers={"Content-Type": "application/json"}, json=payload, auth=HTTPBasicAuth(YOUR_USER, token))
    if response.status_code != 200:
        print(f"Failed to add steps: {response.text}")
    return response.json()

def attach_file_to_jira_issue(jira_base, token, issue_key, file_bytes, filename):
    url = f"{jira_base}/rest/api/3/issue/{issue_key}/attachments"
    headers = {"X-Atlassian-Token": "no-check"}
    files = {"file": (filename, file_bytes)}
    response = requests.post(url, headers=headers, files=files, auth=HTTPBasicAuth(YOUR_USER, token))
    return response.status_code in [200, 201]

# --- TEST CASE GENERATION ---

def generate_test_scripts(requirement_text, context_obj):
    context_str = json.dumps(context_obj, indent=2) if isinstance(context_obj, dict) else str(context_obj)
    prompt = f"""
You are a highly skilled test engineer assistant AI. Your task is to generate precise, step-by-step test scripts in valid JSON format, suitable for direct use in Jira and Excel export.

    IMPORTANT RULES (Do not violate): 
    - DO NOT use Gherkin syntax (NO 'Given', 'When', 'Then'). 
    - DO NOT use bullet points or markdown. - DO NOT explain anything. 
    - DO NOT include comments or headings. 
    - ONLY return a raw JSON array of test steps.

## Instructions:
1. Your input will be a **User Story** (description) and **Acceptance Criteria**.
2. Your task is to break this down into a list of test steps.
3. Each test step must include:
   - "action": a clear user action to perform
   - "data": user input data or parameters used in the step
   - "expected_result": the expected system behavior or outcome
4. The output **must be valid JSON** — a list (array) of objects, each representing a step.
5. Do NOT use Gherkin syntax (no Given/When/Then). Provide clear, direct steps only.
6. Do not include any explanations, markdown code blocks, headings, or comments. Return **only the JSON array**.
7. Ensure the test steps cover all acceptance criteria with 100 percent confidence in completeness and correctness.
8. Avoid empty or null values unless explicitly required.
9. If any important functionality described in the User Story is **not explicitly covered** in the Acceptance Criteria, you must still include test steps for it — as long as it is logically necessary and clearly implied.
10. Your goal is to ensure full coverage of the User Story, even if some acceptance criteria are incomplete or missing.
11. In addition to positive test cases, include **negative test cases** that test invalid inputs, edge cases, or unexpected user actions.
12. Negative test steps should follow the same format and include:
    - "action": the invalid or unexpected user action
    - "data": the incorrect or edge-case input
    - "expected_result": the system's correct handling of the error (e.g., validation message, no action taken, error page)
13. Clearly distinguish negative test steps by including a comment in the "expected_result" like: "This is a negative test case."

---

## Example Output:
[
  {{
    "action": "Open the application in a browser",
    "data": "Application URL",
    "expected_result": "Login page is displayed"
  }},
  {{
    "action": "Click the 'Single Sign-On' button",
    "data": "None",
    "expected_result": "User is authenticated and dashboard is displayed"
  }},
  {{
    "action": "Click the application logo on the dashboard",
    "data": "None",
    "expected_result": "User is redirected to the dashboard"
  }},
  {{
    "action": "Click the 'Home' link in the navigation bar",
    "data": "None",
    "expected_result": "Dashboard screen is displayed with default data"
  }},
  {{
    "action": "Check the top navigation bar",
    "data": "None",
    "expected_result": "Notification bell icon with count is visible"
  }},
  {{
    "action": "Click the notification bell icon",
    "data": "None",
    "expected_result": "Notification panel opens showing list of R files not finalized within 3 days"
  }},
  {{
    "action": "Click a specific notification in the list",
    "data": "FileName.r",
    "expected_result": "Notification shows message 'FileName.r is yet to be finalized' with generation date"
  }}
]
---
Requirement (DO NOT consider this as test steps. It's just a business requirement — not test cases. Ignore any bullets or numbering in it):
Requirement: {requirement_text}
Context: {context_str}
"""

    model_output = call_model(GENERATOR_MODEL_NAME, prompt)
    cleaned = clean_model_output(model_output)
    try:
        return json.loads(cleaned)
    except Exception as e:
        print(f"Model output JSON parse error: {e}")
        return []

def generate_test_cases_from_steps(test_steps):
    return [{
        "Title": f"Test Case {i+1}",
        "Description": step.get("expected_result", ""),
        "Priority": "Medium",
        "Steps": [{
            "Action": step.get("action", ""),
            "Data": step.get("data", ""),
            "ExpectedResult": step.get("expected_result", "")
        }]
    } for i, step in enumerate(test_steps)]

def export_test_scripts_to_csv(test_steps, filename="test_scripts.csv"):
    df = pd.DataFrame([{
        "Step Number": i+1,
        "Action": step.get("action", ""),
        "Data": step.get("data", ""),
        "Expected Result": step.get("expected_result", "")
    } for i, step in enumerate(test_steps)])
    df.to_csv(filename, index=False)
    return filename
