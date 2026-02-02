# 🧠 ITQS AI-Powered Test Case Generator

An intelligent, full-stack tool to **automatically generate high-quality test cases** from user stories, Jira issues, DOCX/PDF files, and more — powered by a custom NLP/AI model.

> Now built with **React (frontend)** and **FastAPI (backend)** for a modern, scalable architecture.

---

## 📐 Architecture

| Layer     | Stack            | Purpose |
|-----------|------------------|---------|
| Frontend  | React + Vite     | UI for uploading, viewing, and exporting test cases |
| Backend   | FastAPI (Python) | API for AI generation, file parsing, Jira integration |
| AI Model  | Cortex API       | Custom LLM for generating test cases from requirements |

---

## 🚀 Key Features

### 📥 Input Options
- 🧾 **Jira Integration** (via JQL)
- ✍️ Manual requirement entry
- 📎 Upload: `.docx`, `.pdf`, `.yaml`, `.json`
- 🌐 Scrape webpage content using AI

### 🤖 AI-Powered Test Case Generation
- Uses your private model hosted at:
https://api.cortex.lilly.com/model/ask/{USER}-gherkin-generator-model

markdown
Copy code
- Generates:
- ✅ Positive
- ❌ Negative
- ⚠️ Edge test cases
- Output formats:
- Plain format
- Gherkin (Given–When–Then)

### 🧹 Deduplication & Validation
- Skips:
- Vague/non-English requirements
- Duplicate titles (if existing test case file uploaded)

### 📊 Rubric Scoring
- Evaluates test cases (score out of 5) based on:
- Total count
- Step detail quality
- Title uniqueness

### 📤 Export & Upload
- Export as `.csv`
- Upload generated test cases to Jira

---

## 🧾 Test Case Output Format

Each test case includes the following fields:

| Field           | Description |
|-----------------|-------------|
| `TestCaseID`     | Unique identifier (e.g., TC-001) |
| `TestCase`       | Title of the test case |
| `Description`    | Brief description of the test case |
| `Action`         | Steps to be performed |
| `Data`           | Input data needed |
| `ExpectedResult` | Expected system behavior or outcome |

### 📄 CSV Example

```csv
TestCaseID,TestCase,Description,Action,Data,ExpectedResult
TC-001,Login with valid credentials,Ensure successful login,Enter valid username and password,username=admin;password=1234,Dashboard is displayed
TC-002,Login with wrong password,Show error for incorrect password,Enter valid username and wrong password,username=admin;password=wrong,Error message shown
🧾 JSON Example
json
Copy code
[
  {
    "TestCaseID": "TC-001",
    "TestCase": "Login with valid credentials",
    "Description": "Ensure successful login",
    "Action": "Enter valid username and password",
    "Data": {
      "username": "admin",
      "password": "1234"
    },
    "ExpectedResult": "Dashboard is displayed"
  }
]
⚙️ Backend Setup (FastAPI)
🔧 Prerequisites
Python 3.8+

Required environment variables:

bash
Copy code
export EMAIL=your.email@domain.com
export USER=yourusername
Or use a .env file:

env
Copy code
EMAIL=your.email@domain.com
USER=yourusername
📦 Install Dependencies
bash
Copy code
cd backend
pip install -r requirements.txt
▶️ Run the API
bash
Copy code
uvicorn main:app --reload
API URL: http://localhost:8000

Swagger UI: http://localhost:8000/docs

💻 Frontend Setup (React)
🔧 Prerequisites
Node.js v18+

NPM or Yarn

📦 Install & Run
bash
Copy code
cd frontend
npm install
npm run dev
App runs at: http://localhost:3000

Connects to backend via proxy or API base URL (http://localhost:8000)

🤖 AI Model Integration
Hosted on Cortex via private endpoint:

ruby
Copy code
https://api.cortex.lilly.com/model/ask/{USER}-gherkin-generator-model
Uses LIGHTClient for secure authentication

Make sure your API access is configured

📎 Supported Upload File Types
File Type	Purpose
.docx, .pdf	Extracts requirements
.yaml, .json	Provides metadata or structured requirements
.csv, .json	Used to avoid generating duplicate test cases

🔄 Jira Integration
Supported Actions
Authenticate using Jira email + API token

Provide:

Jira base URL

JQL query to fetch issues/stories

Select a story to extract requirements

Upload generated test cases as Test issues

Ensure your Jira user has permission to create issues in the selected project.

🧠 Rubric Scoring
Each test case batch is scored (0–5) based on:

Criteria	Description
Count	Total test cases generated
Step Quality	Action & ExpectedResult clarity
Title Uniqueness	Detects and penalizes duplicates
Test Completeness	Checks for missing fields

📤 Export & Upload Options
✅ Export test cases as .csv

⬆️ Upload selected cases to Jira automatically

🗃 Download archive of generated cases locally

🔧 Project Structure
java
Copy code
itqs-ai-test-case-generator/
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── utils/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── .env
└── README.md
✅ Use Cases
QA/Test engineers auto-generating test cases from Jira

Agile teams accelerating test design from requirements

Converting legacy documents into structured test steps

Automating BDD/Non-BDD coverage with Gherkin syntax

👨‍💻 Author
Rishikesh/Neelkanth Dilip
Made with ❤️ for intelligent QA automation

⚠️ Disclaimer
This tool generates test cases using AI. While it improves productivity, always review output before using in production.
