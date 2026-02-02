import os
import re
import json
import yaml
import fitz  # PyMuPDF
from docx import Document
from fastapi import FastAPI, Form, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from requests.auth import HTTPBasicAuth
import requests
import uvicorn
import pandas as pd
import io
from typing import Optional, List, Any
from dotenv import load_dotenv
# from get_all_story_details import extract_text_from_adf
from extract_text_from_adf import extract_text_from_adf
from generate_test_scripts import generate_test_scripts, generate_test_scripts_from_manual_input, validate_testcases
from upload_to_jira_via_Xray import add_jira_test_steps, create_issue, get_internal_issue_id, get_oauth_token, get_test_run_id, link_test_to_execution, update_test_result
from utilities.text_extract import extract_text_from_csv, extract_text_from_docx, extract_text_from_excel, extract_text_from_json, extract_text_from_pdf, extract_text_from_plain_text, extract_text_from_yaml
from helper.transform_test_cases import transform_test_cases
import functools
print = functools.partial(print, flush=True)  # Always flush print output

# sys.stdout.reconfigure(encoding='utf-8')  # Fix UnicodeEncode Error on Windows Console
load_dotenv()

# Environment variables (set EMAIL and USER)
EMAIL = os.getenv("EMAIL")
USER = os.getenv("USER", "")

if not EMAIL or not USER:
    raise EnvironmentError("Environment variables EMAIL and USER must be set.")

CORTEX_BASE = "https://api.cortex.lilly.com"
GENERATOR_MODEL_NAME = f"{USER}-gherkin-generator-model"
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://lilly-jira.atlassian.net")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SAS2R")
ACCEPTANCE_CRITERIA_FIELD_ID = os.getenv("ACCEPTANCE_CRITERIA_FIELD_ID","customfield_10121")

app = FastAPI(title="AI-Powered Test Case Generator API")

# Enable CORS to allow React frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production; restrict to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper Functions and Classes

class JiraFetchRequest(BaseModel):
    jira_base: str = JIRA_BASE_URL
    jira_token: str
    jira_jql: str
    jira_user: str

class GetUserStories(BaseModel):
    jira_api_key: str
    jql: str

class JiraStory(BaseModel):
    key: str
    summary: str
    description: Optional[str]
    acceptance_criteria: Optional[str]

class TestCaseStep(BaseModel):
    """Schema for a single step within a test case."""
    # Renaming 'Step Number' to 'step_number' for Python style while using Field(alias) 
    # to match the original JSON key.
    step_number: int = Field(alias="Step Number")
    action: str = Field(alias="Action")
    data: Any = Field(alias="Data")
    expected_result: str = Field(alias="Expected Result")

class TestCase(BaseModel):
    """Schema for a complete test case."""
    test_case_id: str = Field(alias="Test Case ID")
    title: str = Field(alias="Title")
    description: str = Field(alias="Description")
    steps: List[TestCaseStep] = Field(alias="Steps")

class UploadTestScriptsRequest(BaseModel):
    summary: str
    testScripts: List[TestCase]

class GenerateTestScriptsRequest(BaseModel):
    description: str
    requirement_text: str
    context_json: Optional[dict]


class CreateJiraIssueRequest(BaseModel):
    jira_base: str
    jira_token: str
    project_key: str
    summary: str
    description: str
    priority: str
    issue_type: str = "Test"
    parent_issue_key: str = None


class AddTestStepsRequest(BaseModel):
    jira_base: str
    jira_token: str
    issue_key: str
    steps: list

class Step(BaseModel):
    action: str
    data: str
    expected_result: str

class UploadResponse(BaseModel):
    summary: str
    steps: List[Step]

class ScrapeURLRequest(BaseModel):
    url: str

class ManualInputRequest(BaseModel):
    manual_input: str
    context: Optional[Any] = None

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


def to_adf_format(text: str) -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
    }


def is_valid_requirement(req: str) -> bool:
    if not req or len(req.strip().split()) < 3:
        return False
    if not re.search(r"[a-zA-Z]", req):
        return False
    words = [w.lower() for w in req.split() if re.match(r"^[a-zA-Z]+$", w) and "@" not in w]
    eng_like = [w for w in words if w in ENGLISH_WORDS]
    ratio = len(eng_like) / len(words) if words else 0
    return ratio >= 0.3


# def extract_text_from_pdf(file_bytes) -> str:
#     try:
#         text = ""
#         with fitz.open(stream=file_bytes, filetype="pdf") as doc:
#             for page in doc:
#                 text += page.get_text()
#         return text.strip()
#     except Exception as e:
#         raise ValueError(f"Failed to extract text from PDF: {e}")


# def extract_text_from_docx(file_bytes) -> str:
#     try:
#         from io import BytesIO
#         file_stream = BytesIO(file_bytes)
#         doc = Document(file_stream)
#         return "\n".join(para.text for para in doc.paragraphs).strip()
#     except Exception as e:
#         raise ValueError(f"Failed to extract text from DOCX: {e}")


def clean_model_output(raw_output: str) -> str:
    cleaned = raw_output.strip()
    cleaned = re.sub(r"``````", "", cleaned, flags=re.IGNORECASE).strip()
    match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
    if match:
        return match.group(1)
    return cleaned


def call_cortex_model(prompt: str) -> str:
    url = f"{CORTEX_BASE}/model/ask/{GENERATOR_MODEL_NAME}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data={"q": prompt}, headers=headers)
    response.raise_for_status()
    msg = response.json().get("message", "").strip()
    if not msg:
        raise ValueError("Model returned empty output.")
    return msg


def fetch_jira_issues(jira_jql, jira_token, jira_user):
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    auth = HTTPBasicAuth(jira_user, jira_token)
    jql = f'project={PROJECT_KEY} AND issuetype=Story AND status = Approved ORDER BY created DESC'
    headers = {
        "Accept": "application/json"
    }
    params = {
        "jql": jira_jql,
        "fields": "summary,description,project,customfield_10121",  # or "fields": "*all"
        "maxResults": 100,
        "startAt": 0
    }
    response = requests.get(url, headers=headers, params=params, auth=auth)
    # print(response)
    issues = response.json().get('issues', [])


def create_jira_issue(jira_base, jira_token, project_key, summary, description, priority, issue_type="Test", parent_issue_key=None):
    url = f"{jira_base.rstrip('/')}/rest/api/3/issue"
    auth = HTTPBasicAuth(USER, jira_token)
    headers = {"Content-Type": "application/json"}

    fields = {
        "project": {"key": project_key},
        "summary": summary,
        "description": to_adf_format(description),
        "issuetype": {"name": issue_type},
        "priority": {"name": priority}
    }

    if parent_issue_key:
        fields["parent"] = {"key": parent_issue_key}

    issue_data = {"fields": fields}
    response = requests.post(url, json=issue_data, headers=headers, auth=auth)
    if response.status_code != 201:
        raise HTTPException(status_code=response.status_code,
                            detail=f"Jira issue creation failed: {response.text}")
    return response.json().get("key")


def add_test_steps(jira_base, jira_token, issue_key, steps):
    url = f"{jira_base.rstrip('/')}/rest/raven/1.0/api/test/{issue_key}/step"
    auth = HTTPBasicAuth(USER, jira_token)
    headers = {"Content-Type": "application/json"}

    payload = []
    for idx, step in enumerate(steps):
        payload.append({
            "index": idx,
            "action": step.get("action", ""),
            "result": step.get("expected_result", "")
        })

    response = requests.put(url, json=payload, headers=headers, auth=auth)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code,
                            detail=f"Failed to upload steps: {response.text}")
    return response.json()

def generate_excel_data(test_cases: List['TestCase']) -> io.BytesIO:
    """
    Processes Pydantic TestCase models and generates an Excel file in memory.
    """
    rows = []
    
    # 'test_cases' is now a list of Pydantic TestCase objects
    for tc in test_cases: 
        # Access attributes using dot notation (e.g., tc.test_case_id, NOT tc.get("Test Case ID"))
        
        # 'tc.steps' is a list of Pydantic TestCaseStep objects
        for idx, step in enumerate(tc.steps, 1): 
            # Access step attributes using dot notation (e.g., step.action)
            row = {
                # Only include Test Case ID, Summary, and Description on the first step row
                "Test Case ID": tc.test_case_id if idx == 1 else "",
                "Summary": tc.title if idx == 1 else "",
                "Description": tc.description if idx == 1 else "",
                "Step Number": step.step_number, # Or use idx if you prefer
                "Action": step.action,
                "Data": step.data,
                "Expected Result": step.expected_result
            }
            rows.append(row)
            
    if not rows:
        # Create an empty DataFrame with the required columns
        df_display = pd.DataFrame(columns=["Test Case ID", "Summary", "Description", "Step Number", "Action", "Data", "Expected Result"])
    else:
        df_display = pd.DataFrame(rows)

    # Use BytesIO to write the Excel file to memory
    excel_file = io.BytesIO()
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        df_display.to_excel(writer, index=False, sheet_name='Test Cases')

    excel_file.seek(0)
    return excel_file

# API Endpoints

@app.get("/list-all-projects")
def list_jira_projects():
    url = f"{JIRA_BASE_URL}/rest/api/3/project"
    headers = {"Accept": "application/json"}

    resp = requests.get(url, headers=headers, auth=HTTPBasicAuth(EMAIL, JIRA_API_TOKEN))
    print("Status Code:", resp.status_code)
    print("Raw response:", resp.text)

    if resp.status_code != 200:
        raise Exception(f"Jira API Error: {resp.status_code} {resp.text}")

    return resp.json()


@app.post("/jira/stories", response_model=List[JiraStory])
def get_jira_stories(data: GetUserStories):
    # jql = "project=SAS2R AND issuetype=Story AND status = Approved ORDER BY created DESC"
    url = f"{JIRA_BASE_URL}/rest/api/3/search/jql"
    # Fields to fetch: key, summary, description, acceptance criteria
    fields = ["key", "summary", "description", "customfield_10121"]  # Replace with your actual custom field ID for Acceptance Criteria

    params = {
        "jql": data.jql,
        "fields": ",".join(fields),
        "maxResults": 100  # Adjust as needed (max 1000 per request)
    }

    response = requests.get(
        url,
        params=params,
        auth=HTTPBasicAuth(EMAIL, data.jira_api_key),
        headers={"Accept": "application/json"}
    )
    # print(response.json())
    stories = []
    if response.status_code == 200:
        issues = response.json()['issues']
        for issue in issues:
            issue_key = issue["key"]
            summary = issue["fields"]["summary"]
            description = extract_text_from_adf(issue["fields"].get("description", ""))
            acceptance_criteria = extract_text_from_adf(issue["fields"].get("customfield_10121", ""))
            stories.append({"key":issue_key,"summary":summary,"description":description,"acceptance_criteria":acceptance_criteria})
    else:
        print("Failed to fetch issues:", response.status_code, response.text)       
    return stories


@app.post("/jira/create_issue")
def api_create_jira_issue(data: CreateJiraIssueRequest):
    issue_key = create_jira_issue(
        jira_base=data.jira_base,
        jira_token=data.jira_token,
        project_key=data.project_key,
        summary=data.summary,
        description=data.description,
        priority=data.priority,
        issue_type=data.issue_type,
        parent_issue_key=data.parent_issue_key
    )
    return {"issue_key": issue_key}


@app.post("/jira/add_test_steps")
def api_add_test_steps(data: AddTestStepsRequest):
    response = add_test_steps(data.jira_base, data.jira_token, data.issue_key, data.steps)
    return {"response": response}


# --- QUALITY SCORE FUNCTION ---
def rubric_score(cases_list):
    """
    Calculate quality score for generated test cases (1-5 scale).
    Score deductions:
    - Less than 2 test cases: -1
    - Duplicate titles: -1
    - Empty or insufficient test steps: -1
    """
    score = 5
    
    # Check minimum number of test cases
    if not cases_list or len(cases_list) < 2:
        score -= 1
    
    # Check for duplicate titles
    titles = [c.get("Title", "").strip().lower() for c in cases_list]
    if len(set(titles)) != len(titles):
        score -= 1
    
    # Check for empty or insufficient test steps
    for case in cases_list:
        title = case.get("Title", "").strip()
        steps_data = case.get("Steps", [])
        
        # Penalize empty title
        if not title:
            score -= 1
            break
        
        # Penalize insufficient or empty steps
        if not steps_data:
            score -= 1
            break
        
        # Check if steps have sufficient content
        for step in steps_data:
            action = step.get("Action", "").strip()
            expected = step.get("Expected Result", "").strip()
            if not action or len(expected) < 10:
                score -= 1
                break
    
    return max(score, 1)


@app.post("/generate_test_scripts")
def api_generate_test_scripts(data: GenerateTestScriptsRequest):
    """
    Generate test scripts with quality checking and retry logic.
    Retries up to 3 times if score < 4.
    Returns quality score and generation status.
    """
    max_retries = 3
    best_result = None
    best_score = 0
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n 🔄 Generation Attempt {attempt}/{max_retries}")
            
            # Generate test steps
            test_steps = generate_test_scripts(data.description, data.requirement_text, data.context_json)
            cleaned_cases = transform_test_cases(test_steps)
            
            # Run validator agent (prints detailed breakdown to backend console)
            try:
                validation = validate_testcases(data.requirement_text, data.context_json or "No context provided", json.dumps(cleaned_cases, indent=2))
                v_score = validation.get("score") if isinstance(validation, dict) else None
                print(f" 📊 Validator Score: {v_score}/5")
            except Exception as e:
                print(f" ⚠️ Validator failed: {e}")

            # Calculate quality score (local rubric)
            score = rubric_score(cleaned_cases)
            print(f" 📊 Quality Score: {score}/5")
            print("\n 👉 Test Cases:",json.dumps(cleaned_cases,indent=2),"\n")
            
            # Store best result
            if score > best_score:
                best_score = score
                best_result = {
                    "test_steps": cleaned_cases,
                    "quality_score": score,
                    "generation_attempts": attempt,
                    "quality_status": "PASS" if score >= 4 else "BELOW_THRESHOLD"
                }
            
            # If score meets threshold, return immediately
            if score >= 4:
                print(f" ✅ Quality threshold (4) met on attempt {attempt}")
                return best_result
            
            # If not the last attempt, log retry
            if attempt < max_retries:
                print(f" ⚠️  Score below threshold (4). Retrying...")
        
        except Exception as e:
            print(f" ❌ Error on attempt {attempt}: {str(e)}")
            continue
    
    # Return best attempt if all retries exhausted
    if best_result:
        print(f" ⚠️  Max retries reached. Returning best attempt with score {best_score}")
        return best_result
    
    # Fallback error response
    raise HTTPException(status_code=500, detail="Failed to generate test cases after multiple attempts.")

@app.post("/generate-test-script-from-manual-input")
async def generate_test_script_manual_input(request: ManualInputRequest):
    """
    Generate test scripts from manual input with quality checking and retry logic.
    Retries up to 3 times if score < 4.
    Returns quality score and generation status.
    """
    try:
        context = request.context or "No context provided."  
        
        # Validate the manual input
        if not is_valid_requirement(request.manual_input):
            raise HTTPException(
                status_code=400,
                detail="The provided manual input does not appear to be a valid requirement.",
            )
        
        max_retries = 3
        best_result = None
        best_score = 0
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"\n 🔄 Generation Attempt {attempt}/{max_retries}")
                
                # Generate test scripts using the provided input and context
                test_steps = generate_test_scripts_from_manual_input(request.manual_input, context)
                cleaned_cases = transform_test_cases(test_steps)
                
                # Run validator agent (prints detailed breakdown to backend console)
                try:
                    validation = validate_testcases(request.manual_input, context, json.dumps(cleaned_cases, indent=2))
                    v_score = validation.get("score") if isinstance(validation, dict) else None
                    print(f" 📊 Validator Score: {v_score}/5")
                except Exception as e:
                    print(f" ⚠️ Validator failed: {e}")

                # Calculate quality score
                score = rubric_score(cleaned_cases)
                print(f" 📊 Quality Score: {score}/5")
                print("\n 👉 Test Cases:",json.dumps(cleaned_cases,indent=2),"\n")
                
                # Store best result
                if score > best_score:
                    best_score = score
                    best_result = {
                        "test_steps": cleaned_cases,
                        "quality_score": score,
                        "generation_attempts": attempt,
                        "quality_status": "PASS" if score >= 4 else "BELOW_THRESHOLD"
                    }
                
                # If score meets threshold, return immediately
                if score >= 4:
                    print(f" ✅ Quality threshold (4) met on attempt {attempt}")
                    return best_result
                
                # If not the last attempt, log retry
                if attempt < max_retries:
                    print(f" ⚠️  Score below threshold (4). Retrying...")
            
            except Exception as e:
                print(f" ❌ Error on attempt {attempt}: {str(e)}")
                continue
        
        # Return best attempt if all retries exhausted
        if best_result:
            print(f" ⚠️  Max retries reached. Returning best attempt with score {best_score}")
            return best_result
        
        # Fallback error response
        raise HTTPException(status_code=500, detail="Failed to generate test scripts after multiple attempts.")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate test script from manual input: {str(e)}")


@app.post("/upload-test-scripts-to-jira")
def upload_test_scripts_to_jira(req: UploadTestScriptsRequest):
    xray_token = get_oauth_token()
    print(" Xray token obtained.\n")
    # print(" Received Test Case:", req)
    # for each test case in req: create a test issue in Jira and add steps to it and I need to create a test execution issue and link all the test issues to it and update the test results to ToDo
    test_keys = []
    for test_case in req.testScripts:
        # Create Test Issue
        test_issue = create_issue(test_case.title, "Test")
        test_key = test_issue["key"]
        test_keys.append(test_key)
        test_id = get_internal_issue_id(test_key)
        print(f" 🧪 Created Test issue: {test_key} (id={test_id})")
        add_jira_test_steps(xray_token, test_id, test_case.steps)
    # Create Execution Issue
    print("\n ==> Test Cases created. Now creating Test Execution and linking tests...\n")
    exec_issue = create_issue(f"Execution - {req.summary}", "Test Execution")
    exec_key = exec_issue["key"]
    exec_id = get_internal_issue_id(exec_key)
    print(f"🧪 Created Test Execution: {exec_key} (id={exec_id})")
    # Link all tests to execution and update results
    for test_key in test_keys:
        test_id = get_internal_issue_id(test_key)
        link_test_to_execution(xray_token, exec_id, test_id)
        run_id = get_test_run_id(xray_token, exec_id, test_id)
        if run_id:
            update_test_result(xray_token, run_id, "TODO")
    return {"message": "Test scripts uploaded to Jira successfully.","test_execution_url": f"{JIRA_BASE_URL}/browse/{exec_key}"}
    
    # Create Test
    # test_issue = create_issue(req.summary, "Test")
    # test_key = test_issue["key"]
    # test_id = get_internal_issue_id(test_key)
    # print(f" Created Test issue: {test_key} (id={test_id})")
    # add_jira_test_steps(xray_token, test_id, req.steps)
 
    # # Create Execution
    # exec_issue = create_issue(f"Execution - {req.summary}", "Test Execution")
    # exec_key = exec_issue["key"]
    # exec_id = get_internal_issue_id(exec_key)
    # print(f" Created Test Execution: {exec_key} (id={exec_id})")
 
    # # Link test and update result
    # link_test_to_execution(xray_token, exec_id, test_id)
    # run_id = get_test_run_id(xray_token, exec_id, test_id)
    # if run_id:
    #     update_test_result(xray_token, run_id, "TODO")
 
    # print("✅ All done successfully!")
    # return {"message": "Test scripts uploaded to Jira successfully.", "test_execution_url": f"{JIRA_BASE_URL}/browse/{exec_key}"}

@app.post("/download")
def download_test_scripts_excel(test_cases: List[TestCase]):
    """
    Endpoint to receive test case data and return it as an Excel file.
    """
    try:
        excel_io = generate_excel_data(test_cases)
        
        # Return a StreamingResponse with the Excel file data
        return StreamingResponse(
            # The 'content' must be an iterable of bytes, BytesIO is good here
            content=excel_io, 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                # Tells the browser to download the file and suggests a filename
                'Content-Disposition': 'attachment; filename="test_scripts.xlsx"'
            }
        )
    except Exception as e:
        # Handle potential errors during Excel generation
        print(f"Error during Excel generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate Excel file.")
@app.post("/upload_context")
async def api_extract_text(file: UploadFile = File(...)):
    """
    Upload and extract content from documents.
    Supported document formats: PDF, TXT, JSON, YAML, CSV, Excel (XLS, XLSX), DOCX
    Image/OCR support has been removed.
    """
    file_bytes = await file.read()
    filename = file.filename.lower()

    try:
        # Document formats
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_bytes)
        elif filename.endswith((".txt", ".text")):
            text = extract_text_from_plain_text(file_bytes)
        elif filename.endswith(".docx"):
            text = extract_text_from_docx(file_bytes)
        elif filename.endswith(".json"):
            text = extract_text_from_json(file_bytes)
        elif filename.endswith((".yaml", ".yml")):
            text = extract_text_from_yaml(file_bytes)
        elif filename.endswith(".csv"):
            text = extract_text_from_csv(file_bytes)
        elif filename.endswith((".xls", ".xlsx")):
            text = extract_text_from_excel(file_bytes)
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Supported: PDF, TXT, DOCX, JSON, YAML, CSV, Excel",
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"filename": file.filename, **text}

@app.post("/scrape_url")
def api_scrape_url(request: ScrapeURLRequest):
    try:
        response = requests.get(request.url)
        response.raise_for_status()
        return {"isUrlScraped":True,"context":response.text[:5000],"message":"URL scraped successfully"}  # Return first 5000 chars of raw HTML
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Scraping the URL failed")

@app.get("/")
def root():
    return {"message": "AI-Powered Test Case Generator API is running."}

if __name__ == "__main__":
    uvicorn.run("main:app",host="127.0.0.1", port=8000, reload=True)