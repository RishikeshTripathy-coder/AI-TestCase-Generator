import streamlit as st
import pandas as pd
import numpy as np
import requests
from requests.auth import HTTPBasicAuth
import os
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import io
import datetime
from light_client import LIGHTClient

# --- Streamlit UI ---
st.set_page_config(page_title="Defect Prediction Dashboard", layout="wide")
st.title("🧠 Defects Prevention Tool")

# --- Helper Functions ---

def extract_text_from_description(desc_dict):
    """Extract plain text from Jira description dictionary format"""
    # If it's already a string, return as-is
    if isinstance(desc_dict, str):
        return desc_dict

    # Walk nested structures (dicts/lists) and collect 'text' fields recursively
    texts = []

    def _walk(node):
        if node is None:
            return
        
        if isinstance(node, str):
            texts.append(node)
            return
        if isinstance(node, dict):
            # If this dict directly contains a text field, collect it
            if 'text' in node and isinstance(node['text'], str):
                texts.append(node['text'])
            # Otherwise, iterate all values
            for v in node.values():
                _walk(v)
            return
        if isinstance(node, list):
            for item in node:
                _walk(item)
            return

    _walk(desc_dict)

    if texts:
        # Join collected text fragments with spaces and normalize whitespace
        return ' '.join(t.strip() for t in texts if t and isinstance(t, str))

    # Fallback: stringify the object
    return str(desc_dict)

def fetch_all_projects():
    """Fetch all projects from Jira using API"""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/project"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            url,
            headers=headers,
            auth=HTTPBasicAuth(YOUR_USER, API_TOKEN),
            timeout=10
        )
        
        if response.status_code == 200:
            projects = response.json()
            return projects if isinstance(projects, list) else projects.get('values', [])
        else:
            st.error(f"❌ Error fetching projects: {response.status_code} - {response.text}")
            return []
    
    except Exception as e:
        st.error(f"❌ Failed to fetch projects: {str(e)}")
        return []

def fetch_bugs_for_project(project_key):
    """Fetch all bugs for a specific project from Jira using the new /rest/api/3/search/jql API (POST)."""
    try:
        url = f"https://{JIRA_DOMAIN}/rest/api/3/search/jql"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        # Use issuetype filter and POST body per Jira migration guidance
        jql = f'project = "{project_key}" AND issuetype = Bug'
        payload = {
            "jql": jql,
            "maxResults": 200,
            # request resolutiondate so we can compute aging
            "fields": ["key", "summary", "description", "priority", "created", "status", "resolutiondate"]
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            auth=HTTPBasicAuth(YOUR_USER, API_TOKEN),
            timeout=30
        )

        # Handle migration / removed API message explicitly
        if response.status_code == 410:
            st.error("❌ Jira API endpoint removed (410). Please ensure your Jira instance supports /rest/api/3/search/jql. See: https://developer.atlassian.com/changelog/#CHANGE-2046")
            return []

        if response.status_code != 200:
            st.error(f"❌ Error fetching bugs: {response.status_code} - {response.text}")
            return []

        data = response.json()
        issues = data.get('issues', [])

        bugs = []
        for issue in issues:
            fields = issue.get('fields', {})
            bug = {
                'key': issue.get('key', 'Unknown'),
                'summary': fields.get('summary', 'N/A'),
                'description': fields.get('description', ''),
                'priority': fields.get('priority', {}).get('name', 'N/A'),
                'created': fields.get('created', ''),
                'status': fields.get('status', {}).get('name', 'N/A'),
                'resolutiondate': fields.get('resolutiondate', None)
            }
            bugs.append(bug)

        return bugs

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network/Request error fetching bugs: {e}")
        return []
    except Exception as e:
        st.error(f"❌ Failed to fetch bugs: {str(e)}")
        return []

# --- Cortex API Call to Get Root Cause / Preventive Recommendations ---
def call_model(model_name: str, prompt: str) -> str:
    url = f"{CORTEX_BASE}/model/ask/{model_name}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = client.post(url, data={"q": prompt}, headers=headers)
    response.raise_for_status()
    msg = response.json().get("message", "").strip()
    if not msg:
        raise ValueError("Model returned empty output.")
    return msg

def get_root_cause(description: str) -> str:
    prompt = f"The following is a defect description from a Jira issue. What could be the root cause of this issue? Description: '{description}'"
    try:
        response_text = call_model(GENERATOR_MODEL_NAME, prompt)
        return response_text
    except Exception as e:
        st.error(f"Error during model call: {e}")
        return "Unknown Root Cause"

def get_preventive_recommendations(root_cause_or_category, description="", high_level_cause="", contributing_factor="") -> str:
    """
    Generate preventive recommendations based on:
    1. Root cause hierarchy (for ALM mode)
    2. AI-generated root cause analysis
    
    Combines both for comprehensive prevention strategy.
    """
    if not root_cause_or_category or root_cause_or_category == "Unknown Root Cause":
        return "No recommendations available for unknown root cause."
    
    recommendations_list = []
    
    # Step 1: Get hierarchy-based recommendations for ALM
    if high_level_cause and contributing_factor and high_level_cause in ROOT_CAUSE_HIERARCHY:
        hierarchy_recs = get_alm_recommendations_by_hierarchy(high_level_cause, contributing_factor)
        if hierarchy_recs:
            recommendations_list.append("**Based on Root Cause Hierarchy:**")
            recommendations_list.append(hierarchy_recs)
    
    # Step 2: Get AI-based recommendations from root cause analysis
    prompt = (
        f"The following is the root cause analysis of a defect: '{root_cause_or_category}'. "
        f"Defect description (optional): '{(description or '')[:1000]}'. "
        "Based on this specific root cause, what are the most important prevention and solution steps? "
        "Provide 3-5 specific, actionable recommendations."
    )
    try:
        response_text = call_model(GENERATOR_MODEL_NAME, prompt)
        if response_text:
            recommendations_list.append("\n**Based on Root Cause Analysis:**")
            recommendations_list.append(response_text)
    except Exception as e:
        # Silent fallback if AI call fails
        pass
    
    # If we have recommendations, return combined result
    if recommendations_list:
        return "\n\n".join(recommendations_list)
    
    return "Unable to generate recommendations at this time."

def get_alm_recommendations_by_hierarchy(high_level_cause, contributing_factor):
    """
    Return specific recommendations based on the ALM root cause hierarchy.
    """
    alm_recommendations = {
        "Requirements Issue": {
            "People": [
                "Allocate dedicated domain experts and SMEs to requirement discussions (owner: PM).",
                "Provide BA training on requirement elicitation and documentation techniques (owner: L&D).",
                "Schedule translator/bilingual resources for international teams (owner: HR).",
                "Conduct weekly requirement clarity sessions with business stakeholders (owner: BA/PM).",
                "Document all requirement clarifications in a shared wiki or knowledge base (owner: BA)."
            ],
            "Process": [
                "Implement mandatory requirement review gate with stakeholder sign-off (owner: PM).",
                "Create and enforce requirements questionnaire template (owner: BA).",
                "Require traceability matrix linking requirements to test cases (owner: QA Lead).",
                "Schedule formal requirement walkthroughs before development starts (owner: PM).",
                "Add requirement validation as part of Definition of Done (owner: Scrum Master)."
            ],
            "Tool": [
                "Adopt a requirements management tool (DOORS, Jira, Confluence) (owner: IT/PM).",
                "Provide training on collaboration and documentation tools (owner: IT/L&D).",
                "Enforce tool usage for all requirement documentation (owner: PM).",
                "Set up automated notifications for requirement reviews and approvals (owner: IT).",
                "Create tool templates for consistent requirement capture (owner: BA)."
            ],
            "Environment": [
                "Establish clear communication channels between vendors and team (owner: PM).",
                "Schedule coordination meetings with all stakeholders upfront (owner: PM).",
                "Designate single point of contact for vendor coordination (owner: PM).",
                "Document vendor responsibilities and timelines (owner: PM).",
                "Create contingency plan for vendor coordination failures (owner: PM)."
            ],
            "Material": [
                "Design and enforce standard requirement documentation template (owner: BA).",
                "Create example requirements and best practice guide (owner: BA).",
                "Store templates in shared repository with version control (owner: BA).",
                "Provide training on template usage (owner: L&D).",
                "Review template effectiveness quarterly and update (owner: BA Lead)."
            ]
        },
        "Inadequate Documentation/Configuration": {
            "Process": [
                "Implement parallel testing timelines with buffer time between phases (owner: QA Lead).",
                "Create comprehensive test scenario and case documentation (owner: QA).",
                "Conduct requirement clarity sessions with SMEs before test case creation (owner: QA/BA).",
                "Document all test prerequisites and setup steps in test cases (owner: QA).",
                "Run test case walkthroughs and peer reviews before execution (owner: QA Lead)."
            ]
        },
        "Incorrect Testing": {
            "People": [
                "Provide comprehensive QA training covering boundary conditions and edge cases (owner: L&D).",
                "Create boundary test case templates and checklists (owner: QA Lead).",
                "Implement mandatory peer review for all test scripts (owner: QA Lead).",
                "Conduct test case walkthroughs with team before execution (owner: QA Lead).",
                "Schedule refresher training on role-based security testing (owner: L&D).",
                "Create test data requirement checklist and validation process (owner: QA).",
                "Document expected outputs with baseline values and references (owner: QA).",
                "Implement test case versioning tied to application role/permission changes (owner: QA Lead)."
            ]
        },
        "Standards Violation": {
            "Process": [
                "Implement sequential testing phases with clear entry/exit criteria (owner: QA Lead).",
                "Establish testing gates that prevent parallel UAT and System testing (owner: QA Lead).",
                "Allocate adequate time for pre-testing activities in project schedule (owner: PM).",
                "Define standards and non-negotiable compliance checks (owner: QA Lead).",
                "Add standards validation as part of code review checklist (owner: Dev Lead)."
            ]
        },
        "Inadequate Environment/Infrastructure": {
            "Environment": [
                "Create environment parity checklist (dev, test, FIT, prod match) (owner: DevOps).",
                "Document all environment configurations in version control (owner: DevOps).",
                "Automate environment provisioning and configuration (owner: DevOps).",
                "Create runbook for reproducing issues across environments (owner: DevOps/QA).",
                "Add smoke tests after deployment to verify environment health (owner: QA)."
            ]
        },
        "Lack of Test Data": {
            "People": [
                "Create comprehensive test data requirement checklist (owner: QA).",
                "Document all preconditions and data dependencies for test cases (owner: QA).",
                "Implement test data validation process before test execution (owner: QA).",
                "Create test data management and traceability matrix (owner: QA).",
                "Schedule test data preparation and validation sessions (owner: QA Lead)."
            ]
        }
    }
    
    if high_level_cause in alm_recommendations:
        if contributing_factor in alm_recommendations[high_level_cause]:
            recs = alm_recommendations[high_level_cause][contributing_factor]
            return "\n".join([f"- {r}" for r in recs])
    
    return None

# New: 5-Level Root Cause Hierarchy for ALM Defect Analysis
# High Level Cause -> Contributing Factor -> Level 1-5 Causes
ROOT_CAUSE_HIERARCHY = {
    "Requirements Issue": {
        "People": {
            "level_1": [
                "Lack of business knowledge among business analysts",
                "Inadequate documentation of requirements",
                "Lack of clarity to the Customer",
                "Inadequate communication of requirement",
                "Requirements misunderstood by business analyst"
            ],
            "level_2": [
                "Domain experts not available",
                "Language constraints - end users not English speakers",
                "Market needs changing dynamically",
                "Language constraint to Customer"
            ],
            "level_3": [
                "Not enough time to release from other engagements",
                "Translators could not be allocated"
            ],
            "level_4": [
                "Resource planning not done upfront"
            ]
        },
        "Process": {
            "level_1": [
                "Requirements questionnaire not used",
                "No reviews done on requirements document",
                "Signoff not obtained from Customer"
            ],
            "level_2": [
                "Lack of awareness of Requirements questionnaire",
                "Requirement reviews not planned"
            ],
            "level_3": [
                "Inadequate training on Requirements questionnaire"
            ]
        },
        "Tool": {
            "level_1": [
                "No tool used to develop requirements"
            ],
            "level_2": [
                "Collaboration tool not planned"
            ],
            "level_3": [
                "Lack of tool planning at project initiation"
            ],
            "level_4": [
                "Lack of awareness of usage of collaboration tool"
            ],
            "level_5": [
                "Inadequate training on tool usage for requirements"
            ]
        },
        "Environment": {
            "level_1": [
                "Multiple vendors involved in capturing requirements"
            ],
            "level_2": [
                "Lack of coordination among multiple stakeholders"
            ],
            "level_3": [
                "Inadequate planning for requirements capturing"
            ]
        },
        "Material": {
            "level_1": [
                "No template to document requirements"
            ],
            "level_2": [
                "Template for capturing inputs not designed"
            ],
            "level_3": [
                "Template requirement not analyzed"
            ],
            "level_4": [
                "Inadequate planning for requirements capturing"
            ]
        }
    },
    "Inadequate Documentation/Configuration": {
        "Process": {
            "level_1": [
                "UAT defect - not caught during System Testing",
                "Requirement misunderstood",
                "Prerequisites not executed correctly",
                "Outbound scenario not documented"
            ],
            "level_2": [
                "Scenario not tested in system testing",
                "Requirements not properly cleared during discussion",
                "Tester missed to execute prerequisites",
                "High level requirements drafted but not detailed"
            ],
            "level_3": [
                "UAT and System testing started in parallel",
                "Best Practice of Testing (SME session) not occurred",
                "Human error by tester",
                "Outbound scenario discussed over call but not documented"
            ],
            "level_4": [
                "Delay in pre-testing activities shrink testing cycle",
                "Insufficient window given for test case designing"
            ]
        }
    },
    "Incorrect Testing": {
        "People": {
            "level_1": [
                "Boundary conditions not verified properly",
                "Formatting not verified properly",
                "Test Script Defect - incorrect steps",
                "Expected output incorrectly defined",
                "Tester reported defect that didn't exist",
                "Test cases not aligned with current system roles/permissions"
            ],
            "level_2": [
                "Testers missed boundary condition coverage",
                "Testers missed cosmetic verifications",
                "Tester misunderstood intended workflow",
                "Based on outdated/incorrect reference",
                "Functionality tested without all preconditions",
                "Test cases originally created by another team - not updated"
            ],
            "level_3": [
                "Testers taken initial training but need extensive training",
                "Test case created without reviewing system behavior",
                "No baseline or review of expected values",
                "Tester didn't validate previous script",
                "Preconditions missed - test case didn't specify setup",
                "Lack of visibility regarding security roles required"
            ],
            "level_4": [
                "No peer review or walkthrough for script",
                "No traceability or precondition checklist",
                "Insufficient communication between testing and development",
                "No defined process to review/update test cases based on role changes"
            ]
        }
    },
    "Standards Violation": {
        "Process": {
            "level_1": [
                "UAT defect - not caught during System Testing"
            ],
            "level_2": [
                "Scenario not tested in system testing"
            ],
            "level_3": [
                "UAT and System testing started in parallel"
            ],
            "level_4": [
                "Delay in pre-testing activities shrink testing cycle"
            ]
        }
    },
    "Inadequate Environment/Infrastructure": {
        "Environment": {
            "level_1": [
                "UAT defect - not caught during System Testing"
            ],
            "level_2": [
                "Scenario not reproducible in FIT Environment"
            ],
            "level_3": [
                "Issue raised by end user in Prod Environment"
            ]
        }
    },
    "Lack of Test Data": {
        "People": {
            "level_1": [
                "Tester reported defect that didn't exist",
                "Functionality tested without all preconditions"
            ],
            "level_2": [
                "Tester didn't validate previous script",
                "Preconditions were missed"
            ],
            "level_3": [
                "No traceability or precondition checklist"
            ]
        }
    }
}

# Simplified keywords for initial categorization
CATEGORY_KEYWORDS = {
    "Requirements Issue": ["requirements", "requirement", "specification", "inadequate documentation", "lack of clarity", "requirements misunderstood"],
    "Inadequate Documentation/Configuration": ["documentation", "configuration", "config", "uat defect", "system testing", "misunderstood", "prerequisite"],
    "Incorrect Testing": ["test", "testing", "boundary", "verification", "test script", "expected output", "tester", "precondition"],
    "Standards Violation": ["standards", "violation", "rule", "compliance", "non-compliance"],
    "Inadequate Environment/Infrastructure": ["environment", "infrastructure", "deployment", "prod", "fit", "reproducible", "configuration issue"],
    "Lack of Test Data": ["test data", "data", "precondition", "preconditions"]
}

def map_to_category(text):
    """
    Map text to one of the ALM root cause categories using keyword matching.
    Returns tuple: (High Level Cause, Contributing Factor, Detailed Path)
    """
    if not text or not isinstance(text, str):
        return "Unknown", "Unknown", []
    
    text_l = text.lower()
    
    # Score each high-level category
    scores = {}
    for high_level, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_l)
        scores[high_level] = score
    
    best_high_level = max(scores.items(), key=lambda x: x[1])[0] if scores else "Unknown"
    
    if best_high_level == "Unknown" or best_high_level not in ROOT_CAUSE_HIERARCHY:
        return best_high_level, "Unknown", []
    
    # Determine contributing factor based on additional keywords
    hierarchy = ROOT_CAUSE_HIERARCHY[best_high_level]
    contributing_scores = {}
    
    for factor, levels in hierarchy.items():
        # Extract all keywords from all levels
        all_keywords = []
        for level_key in levels:
            all_keywords.extend(levels[level_key])
        factor_score = sum(1 for kw in all_keywords if kw.lower() in text_l)
        contributing_scores[factor] = factor_score
    
    best_factor = max(contributing_scores.items(), key=lambda x: x[1])[0] if contributing_scores else "Unknown"
    
    # Build detailed path through the hierarchy
    detailed_path = []
    if best_factor in hierarchy:
        levels = hierarchy[best_factor]
        for level_name in sorted(levels.keys()):
            matched_causes = [cause for cause in levels[level_name] if cause.lower() in text_l]
            if matched_causes:
                detailed_path.append({level_name: matched_causes})
    
    return best_high_level, best_factor, detailed_path

def format_root_cause_path(high_level, contributing_factor, detailed_path):
    """Format the root cause hierarchy path for display"""
    if not high_level or high_level == "Unknown":
        return "Unknown Root Cause"
    
    parts = [f"**High Level Cause:** {high_level}"]
    if contributing_factor and contributing_factor != "Unknown":
        parts.append(f"**Contributing Factor:** {contributing_factor}")
    
    if detailed_path:
        for item in detailed_path:
            for level_name, causes in item.items():
                if causes:
                    causes_text = ", ".join(causes[:2])  # Show first 2 matches
                    parts.append(f"**{level_name.replace('_', ' ').title()}:** {causes_text}")
    
    return "\n".join(parts)

# --- Initialize session state for configuration ---
if 'jira_configured' not in st.session_state:
    st.session_state.jira_configured = False
    st.session_state.stored_jira_url = ""
    st.session_state.stored_api_token = ""
    st.session_state.stored_email = ""

# --- Check if already configured ---
if not st.session_state.jira_configured:
    # --- Jira Configuration Section (Center Page) ---
    st.subheader("⚙️ Jira Configuration")
    st.info("ℹ️ Please enter your Jira credentials to proceed.")
    
    config_col1, config_col2, config_col3 = st.columns(3)
    
    with config_col1:
        jira_url_input = st.text_input("🔗 Jira URL", placeholder="e.g., https://lilly-jira.atlassian.net", key="jira_url_input")
    
    with config_col2:
        api_token_input = st.text_input("🔑 API Token", type="password", placeholder="Your API Token", key="api_token_input")
    
    with config_col3:
        email_input = st.text_input("📧 Email", placeholder="Your Jira email", key="email_input")
    
    if st.button("✅ Connect to Jira", width='stretch'):
        if not jira_url_input or not api_token_input or not email_input:
            st.error("❌ Please fill in all fields to proceed.")
        else:
            st.session_state.jira_configured = True
            st.session_state.stored_jira_url = jira_url_input
            st.session_state.stored_api_token = api_token_input
            st.session_state.stored_email = email_input
            st.rerun()
    
    st.stop()

# --- Use stored configuration ---
YOUR_USER = st.session_state.stored_email
JIRA_DOMAIN = st.session_state.stored_jira_url.replace("https://", "").replace("http://", "")
API_TOKEN = st.session_state.stored_api_token
CORTEX_BASE = "https://api.cortex.lilly.com"
GENERATOR_MODEL_NAME = "jira-automation-lilly-openai-v21"

client = LIGHTClient()

# --- Display Configuration Status ---
st.success(f"✅ Connected to Jira | Email: {YOUR_USER}")
if st.button("🔄 Change Jira Configuration"):
    st.session_state.jira_configured = False
    st.session_state.stored_jira_url = ""
    st.session_state.stored_api_token = ""
    st.session_state.stored_email = ""
    st.rerun()

st.divider()

# --- Mode Selection (Jira vs File Upload) ---
mode = st.radio("Choose Data Source", ("Fetch Bugs from Jira", "Upload File Manually"), index=None)

# --- EARLY EXIT: If no mode selected, stop here ---
if mode is None:
    st.info("ℹ️ Please select a data source above to continue.")
    st.stop()

# Function to preprocess descriptions
def preprocess_descriptions(bugs, desc_field='description', key_field='key', is_alm_manual=False):
    """
    When is_alm_manual=True, prefer 'Root Cause Description' as description and 'Root Cause Category' as summary/category
    """
    nlp = spacy.load("en_core_web_sm")
    processed = []
    valid_bugs = []
    
    for bug in bugs:
        # For ALM/manual uploads always use 'Root Cause Description' for clustering, fallback to empty string
        if is_alm_manual:
            desc = bug.get('Root Cause Description', '')
            summary = bug.get('Root Cause Category', '') or bug.get('summary', '')
            bug['summary'] = summary
        else:
            desc = bug.get(desc_field, '') or bug.get('description', '')
        key = bug.get(key_field, bug.get('Defect Id', bug.get('key', 'Unknown')))

        if isinstance(desc, dict):
            desc = extract_text_from_description(desc)

        # If still not a string, fallback to empty string
        if not isinstance(desc, str):
            desc = ''

        if not desc.strip():
            # Skip if no usable description
            continue

        doc = nlp(str(desc))
        tokens = [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]
        cleaned = " ".join(tokens)

        if cleaned.strip():
            processed.append(cleaned)
            # ensure key field present for downstream
            bug['key'] = key
            # For ALM/manual, also set 'description' to 'Root Cause Description' for downstream use
            if is_alm_manual:
                bug['description'] = bug.get('Root Cause Description', '')
            else:
                bug['description'] = desc
            valid_bugs.append(bug)
    return processed, valid_bugs

# Function to cluster defects
def cluster_defects(descriptions, bugs, num_clusters=3):
    if len(descriptions) < num_clusters:
        num_clusters = max(1, len(descriptions))
    
    vectorizer = TfidfVectorizer(max_features=200)
    X = vectorizer.fit_transform(descriptions)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    labels = kmeans.fit_predict(X)
    for i, bug in enumerate(bugs):
        bug['cluster'] = int(labels[i])
        # Map to one of the high-level categories using description (ALM-specific hierarchy)
        desc = bug.get('description', '') or bug.get('Root Cause Description', '')
        high_level, contributing_factor, detailed_path = map_to_category(desc)
        bug['mapped_category'] = high_level
        bug['contributing_factor'] = contributing_factor
        bug['root_cause_path'] = detailed_path
    return bugs

# Function to display bug analysis
def display_bug_analysis(df, is_jira_mode=False):
    # Add month column
    df = add_month_column(df, date_col='created')
    
    st.subheader("🔍 Filters & Overview")
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        if 'mapped_category' in df.columns:
            cats = sorted(df['mapped_category'].fillna("Other").unique())
            selected_cats = st.multiselect("Select Mapped Category", options=cats, default=cats, key="cat_filter")
            # If user clears the selection, treat it as 'select all' to avoid empty results/navigation
            if not selected_cats:
                selected_cats = cats
            df = df[df['mapped_category'].isin(selected_cats)]
    with filter_col2:
        # Use stringified month values to avoid Period/NaT issues
        df['month_str'] = df['month'].astype(str).fillna("Unknown")
        months = sorted(df['month_str'].unique())
        selected_months = st.multiselect("Select Month", options=months, default=months, key="month_filter")
        # If user clears month selection, interpret as 'all months' to avoid empty dataframe and unexpected navigation
        if not selected_months:
            selected_months = months
            st.info("No months selected — showing all months.")
        df = df[df['month_str'].isin(selected_months)]
    
    st.subheader("📊 Defects by Month")
    month_counts = df.groupby('month').size().reindex(months, fill_value=0)
    st.bar_chart(month_counts)

    st.subheader("📊 Defects by Mapped Category")
    cat_counts = df['mapped_category'].value_counts()
    st.bar_chart(cat_counts)

    st.subheader("📈 Sample Defects")
    display_cols = ['key', 'summary', 'mapped_category', 'cluster', 'month']
    if 'priority' in df.columns:
        display_cols.append('priority')
    display_cols = [c for c in display_cols if c in df.columns]
    # Show all fields for both Jira and ALM/manual modes to provide full context
    st.dataframe(df.head(50), width='stretch')

    # --- Enhanced Preventive Recommendations with Full Defect Details ---
    st.subheader("💡 Defect Analysis & Prevention Recommendations")
    st.write("---")
    
    for idx, row in df.iterrows():
        # Extract key fields based on mode
        if is_jira_mode:
            defect_id = row.get('key', 'N/A')
            defect_summary = row.get('summary', 'N/A')
            defect_description = row.get('description', '')
            root_cause_category = row.get('mapped_category', 'Unknown')
        else:
            # ALM/Manual upload mode
            defect_id = row.get('Defect Id', row.get('key', 'N/A'))
            defect_summary = row.get('summary', row.get('Root Cause Category', 'N/A'))
            defect_description = row.get('description', row.get('Root Cause Description', ''))
            root_cause_category = row.get('mapped_category', row.get('Root Cause Category', 'Unknown'))
        
        # Create expandable section for each defect
        # For ALM/manual mode show a snippet of the Description in the expander title
        expander_title_snippet = (defect_description[:60] if not is_jira_mode else defect_summary[:60])
        with st.expander(f"🔍 {defect_id} — {expander_title_snippet}...", expanded=False):
            # Defect Details Section
            st.subheader("📋 Defect Details")
            detail_col1, detail_col2 = st.columns(2)
            
            with detail_col1:
                st.write(f"**Defect ID:** {defect_id}")
                st.write(f"**Summary:** {defect_summary}")
                st.write(f"**Category:** {root_cause_category}")
                if 'cluster' in row and pd.notna(row['cluster']):
                    st.write(f"**Cluster:** {row['cluster']}")
            
            with detail_col2:
                if 'priority' in row and pd.notna(row['priority']):
                    st.write(f"**Priority:** {row['priority']}")
                if 'status' in row and pd.notna(row['status']):
                    st.write(f"**Status:** {row['status']}")
                if 'created' in row and pd.notna(row['created']):
                    st.write(f"**Created:** {row['created']}")
                if 'month' in row and pd.notna(row['month']):
                    st.write(f"**Month:** {row['month']}")
            
            # Description Section
            st.subheader("📝 Description")
            st.write(f"{defect_description[:500]}..." if len(str(defect_description)) > 500 else defect_description)
            
            # Root Cause Analysis Section
            st.subheader("🔎 Root Cause Analysis")
            with st.spinner(f"Analyzing root cause for {defect_id}..."):
                root_cause = get_root_cause(defect_description)
            st.write(f"**Root Cause:** {root_cause}")
            
            # Mapped Category Info - Detailed hierarchy for both modes
            st.subheader("📊 Root Cause Analysis Hierarchy")
            high_level = row.get('mapped_category', 'Unknown')
            contributing = row.get('contributing_factor', 'Unknown')
            path = row.get('root_cause_path', [])
            
            st.write(f"**High Level Cause:** {high_level}")
            st.write(f"**Contributing Factor:** {contributing}")
            
            if path:
                st.write("**Root Cause Path:**")
                for item in path:
                    for level_name, causes in item.items():
                        if causes:
                            level_display = level_name.replace('_', ' ').title()
                            st.write(f"  - **{level_display}:** {', '.join(causes[:2])}")
            
            # Root Cause Description (for ALM mode)
            if not is_jira_mode and 'Root Cause Description' in row:
                st.write(f"**Root Cause Description:** {row.get('Root Cause Description', 'N/A')}")
            
            # Prevention & Solution Section
            st.subheader("✅ Defect Prevention & Solution")
            with st.spinner(f"Generating prevention recommendations for {defect_id}..."):
                # Use hierarchy-based recommendations for both Jira and ALM modes
                high_level = row.get('mapped_category', 'Unknown')
                contributing = row.get('contributing_factor', 'Unknown')
                # For ALM/manual uploads, present the ALM defect Description as the Summary here
                if not is_jira_mode:
                    st.write(f"**Summary:** {defect_description}")
                # Show the Description used to generate recommendations (explicit label)
                st.write(f"**Description Used For Recommendations:** {defect_description}")
                recommendations = get_preventive_recommendations(
                    root_cause,
                    defect_description,
                    high_level_cause=high_level,
                    contributing_factor=contributing
                )
            
            st.write("**Recommended Preventive Actions:**")
            st.write(recommendations)
            
            # Additional Context
            st.subheader("📌 Additional Context")
            context_items = []
            if 'Root Cause Category' in row:
                context_items.append(f"- **Root Cause Category:** {row['Root Cause Category']}")
            if 'priority' in row:
                context_items.append(f"- **Priority:** {row['priority']}")
            if len(context_items) > 0:
                st.write("\n".join(context_items))
            else:
                st.write("No additional context available.")
            
            st.divider()

def display_dashboard(df, is_jira_mode=False):
    """Show a high-level dashboard: KPIs, clusters, top mapped categories and preventive actions."""
    # Ensure month and aging are present
    df = add_month_column(df, date_col='created')
    df = compute_aging(df)

    st.subheader("📊 Dashboard Overview")

    # KPIs
    total_defects = len(df)
    nota_defects = 0
    if 'Root Cause Category' in df.columns:
        nota_defects = df[df['Root Cause Category'] == 'Not a Defect'].shape[0]
    defect_count = total_defects - nota_defects
    defect_accuracy = (defect_count / total_defects) * 100 if total_defects > 0 else 0
    avg_aging = df['aging_days'].dropna().mean() if 'aging_days' in df.columns else None

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📊 Total Defects", total_defects)
    k2.metric("✅ Actual Defects", defect_count)
    k3.metric("📈 Defect Accuracy", f"{defect_accuracy:.2f}%")
    k4.metric("⏳ Avg Defect Aging (days)", f"{avg_aging:.1f}" if pd.notna(avg_aging) else "N/A")

    st.divider()

    # Clusters
    st.subheader("🧩 Defect Clusters")
    if 'cluster' in df.columns:
        cluster_counts = df['cluster'].value_counts().sort_index()
        st.bar_chart(cluster_counts)
        st.write(cluster_counts.to_frame(name='count'))
    else:
        st.info("No cluster information available.")

    # Top mapped categories
    st.subheader("🏷️ Top Mapped Root Cause Categories")
    if 'mapped_category' in df.columns:
        top_cats = df['mapped_category'].value_counts().head(5)
        st.bar_chart(top_cats)

        # Show top 3 with preventive actions
        st.write("**Top Categories & Preventive Actions**")
        for cat, cnt in top_cats.head(3).items():
            with st.expander(f"{cat} — {cnt} defects", expanded=False):
                st.write(f"**Category:** {cat}")
                # Try to provide hierarchy-based recommendations
                try:
                    recs = get_preventive_recommendations(cat, description="", high_level_cause=cat, contributing_factor="Unknown")
                    st.write(recs)
                except Exception:
                    st.write("No recommendations available.")
    else:
        st.info("No mapped category information available.")

    st.divider()

    # Recent defects sample
    st.subheader("📝 Recent Defects")
    sample_cols = df.columns.tolist()
    sort_cols = ['created'] if 'created' in df.columns else sample_cols
    try:
        st.dataframe(df[sample_cols].sort_values(by=sort_cols).head(50), width='stretch')
    except Exception:
        st.dataframe(df[sample_cols].head(50), width='stretch')

    st.write("---")
    st.write("Use the Detailed Defect Analysis view to inspect individual defects and prevention recommendations.")

# Monthly aggregation helper
def add_month_column(df, date_col='created'):
    """Add a 'month' column in YYYY-MM format based on date_col if available."""
    # Try to coerce a created-like date into a consistent month string.
    # If the provided date_col is missing or parsing fails, attempt to detect common date columns.
    if date_col not in df.columns or df[date_col].isna().all():
        # Try other common names
        detected, _ = detect_date_columns(df)
        if detected:
            date_col = detected

    if date_col in df.columns:
        try:
            # Parse datetimes robustly (accept many formats and timezone-aware strings)
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce', utc=True)
            # Convert to local naive timestamps (drop timezone) for consistent month extraction
            if df[date_col].dt.tz is not None:
                df[date_col] = df[date_col].dt.tz_convert(None)
            df['month'] = df[date_col].dt.to_period('M').astype(str)
        except Exception:
            df['month'] = "Unknown"
    else:
        df['month'] = "Unknown"

    # Ensure month column is string and replace any NaT/NaN with 'Unknown'
    df['month'] = df['month'].astype(str).fillna("Unknown")
    return df

def detect_date_columns(df):
    """Return best guesses for (detected_date_col, closed_date_col) from common names."""
    cols = list(df.columns)
    lc = {c.lower(): c for c in cols}
    detected_candidates = [
        'created', 'detected on', 'detected', 'detected_date', 'detected on date',
        'detectedon', 'date_detected', 'start_date'
    ]
    closed_candidates = [
        'resolutiondate', 'resolved', 'resolved on', 'resolved_date', 'closed',
        'closed on', 'closeddate', 'date_closed', 'end_date'
    ]

    detected_col = None
    closed_col = None

    for cand in detected_candidates:
        if cand in lc:
            detected_col = lc[cand]
            break
    for cand in closed_candidates:
        if cand in lc:
            closed_col = lc[cand]
            break

    return detected_col, closed_col


def compute_aging(df):
    """
    Compute aging_days column where possible.
    Looks for 'created' / 'resolutiondate' (or other detected/closed columns).
    Adds 'aging_days' (float) to df and returns df.
    """
    df = df.copy()

    # Candidate names for start/end dates (case-sensitive keys preserved by matching lowercased names)
    start_candidates = [
        'created', 'Created', 'detected on', 'Detected On', 'detected', 'Detected',
        'detected_date', 'Detected Date', 'start_date'
    ]
    end_candidates = [
        'resolutiondate', 'resolutionDate', 'resolved', 'Resolved', 'resolved on',
        'Resolved On', 'resolved_date', 'Resolved Date', 'closed', 'Closed',
        'closed on', 'Closed On', 'closeddate', 'date_closed', 'end_date'
    ]

    start_col = None
    end_col = None

    for c in start_candidates:
        if c in df.columns:
            start_col = c
            break
    for c in end_candidates:
        if c in df.columns:
            end_col = c
            break

    # fallback to detect_date_columns if not found
    if not start_col or not end_col:
        detected, closed = detect_date_columns(df)
        start_col = start_col or detected
        end_col = end_col or closed

    # Normalize to datetime
    if start_col:
        # parse with utc=True to avoid mixed-timezone future warnings and normalize values
        df['_start_dt'] = pd.to_datetime(df[start_col], errors='coerce', utc=True)
    else:
        df['_start_dt'] = pd.NaT

    if end_col:
        # parse with utc=True to avoid mixed-timezone future warnings and normalize values
        df['_end_dt'] = pd.to_datetime(df[end_col], errors='coerce', utc=True)
    else:
        df['_end_dt'] = pd.NaT

    # Compute aging in days (end - start). If end missing, aging will be NaN.
    # Perform per-row safe subtraction to handle tz-aware vs tz-naive mix.
    def _compute_days(end, start):
        try:
            if pd.isna(end) or pd.isna(start):
                return np.nan

            # If objects are pandas Timestamp, ensure they are timezone-aware consistently
            # If one is tz-aware and the other is naive, assume naive timestamps are UTC and localize them
            end_tz = getattr(end, 'tzinfo', None)
            start_tz = getattr(start, 'tzinfo', None)

            if end_tz is None and start_tz is not None:
                # make end timezone-aware (assume UTC)
                if isinstance(end, (pd.Timestamp, datetime.datetime)):
                    end = pd.to_datetime(end, errors='coerce', utc=True)
                else:
                    end = pd.to_datetime(end, errors='coerce', utc=True)

            if start_tz is None and end_tz is not None:
                if isinstance(start, (pd.Timestamp, datetime.datetime)):
                    start = pd.to_datetime(start, errors='coerce', utc=True)
                else:
                    start = pd.to_datetime(start, errors='coerce', utc=True)

            # Use pandas to compute difference (result is Timedelta)
            delta = pd.to_datetime(end, errors='coerce', utc=True) - pd.to_datetime(start, errors='coerce', utc=True)
            if pd.isna(delta):
                return np.nan
            return (delta / np.timedelta64(1, 'D'))
        except Exception:
            return np.nan

    df['aging_days'] = df.apply(lambda r: _compute_days(r.get('_end_dt'), r.get('_start_dt')), axis=1).astype('float')

    # Treat negative durations as NaN
    df.loc[df['aging_days'] < 0, 'aging_days'] = pd.NA

    # Clean up temp columns
    df.drop(columns=['_start_dt', '_end_dt'], inplace=True, errors='ignore')

    return df

# --- Fetch Data / UI Based on Mode ---
if mode == "Fetch Bugs from Jira":
    st.subheader("📁 Select Project to Fetch Bugs")

    with st.spinner("Fetching projects from Jira..."):
        projects = fetch_all_projects()
    
    if not projects:
        st.error("❌ Failed to fetch projects. Please check your Jira configuration.")
    else:
        project_options = [f"{p['key']} - {p['name']}" for p in projects]
        project_select_options = ["All Projects"] + project_options
        selected_project = st.selectbox("📁 Select Project (or choose All Projects)", project_select_options)

        if selected_project:
            # If user chooses All Projects, fetch bugs across every project and aggregate
            if selected_project == "All Projects":
                if st.button("🔍 Fetch Bugs for All Projects"):
                    with st.spinner("Fetching bugs from all Jira projects..."):
                        all_bugs = []
                        for p in projects:
                            key = p.get('key')
                            try:
                                bugs = fetch_bugs_for_project(key)
                                if bugs:
                                    # tag each bug with its project key for clarity
                                    for b in bugs:
                                        b['project'] = key
                                    all_bugs.extend(bugs)
                            except Exception as e:
                                st.warning(f"Failed to fetch for project {key}: {e}")

                    if all_bugs:
                        st.subheader(f"✅ Fetched {len(all_bugs)} bugs across {len(projects)} projects")
                        descriptions, valid_bugs = preprocess_descriptions(all_bugs, desc_field='description', key_field='key', is_alm_manual=False)
                        if not descriptions:
                            st.warning("❌ No valid descriptions found for clustering. Please check Jira data.")
                        else:
                            clustered_bugs = cluster_defects(descriptions, valid_bugs)
                            df = pd.DataFrame(clustered_bugs)
                            # Add aging and month columns for Jira data
                            df = compute_aging(df)
                            df = add_month_column(df, date_col='created')
                            # Store prepared DataFrame in session state so view persists across reruns
                            st.session_state['analysis_df'] = df
                            st.session_state['analysis_is_jira'] = True
                            st.session_state['analysis_source'] = 'all_projects'
                            st.success(f"✅ Prepared {len(df)} bugs for analysis across all projects. Use the View selector below.")
                    else:
                        st.warning("❌ No bugs found across selected projects")
            else:
                selected_key = selected_project.split(" - ")[0]
                if st.button("🔍 Fetch Bugs"):
                    with st.spinner("Fetching bugs from Jira..."):
                        all_bugs = fetch_bugs_for_project(selected_key)

                    if all_bugs:
                        st.subheader(f"✅ Fetched {len(all_bugs)} bugs")
                        descriptions, valid_bugs = preprocess_descriptions(all_bugs, desc_field='description', key_field='key', is_alm_manual=False)

                        if not descriptions:
                            st.warning("❌ No valid descriptions found for clustering. Please check Jira data.")
                        else:
                            clustered_bugs = cluster_defects(descriptions, valid_bugs)
                            df = pd.DataFrame(clustered_bugs)
                            # Add aging and month columns for Jira data
                            df = compute_aging(df)
                            df = add_month_column(df, date_col='created')
                            # Store prepared DataFrame in session state so view persists across reruns
                            st.session_state['analysis_df'] = df
                            st.session_state['analysis_is_jira'] = True
                            st.session_state['analysis_source'] = selected_key
                            st.success(f"✅ Prepared {len(df)} bugs for analysis for project {selected_key}. Use the View selector below.")
                    else:
                        st.warning(f"❌ No bugs found for project {selected_key}")

elif mode == "Upload File Manually":

    st.subheader("📁 Upload Your Files to Analyze Bugs (Multiple Supported)")
    uploaded_files = st.file_uploader("Upload one or more raw Jira Bugs Excel files", type=["xlsx"], accept_multiple_files=True)

    if uploaded_files:
        dfs = []
        for uploaded_file in uploaded_files:
            try:
                df = pd.read_excel(uploaded_file)
                # Add a Project column based on file name (without extension)
                project_name = os.path.splitext(uploaded_file.name)[0]
                df['Project'] = project_name
                dfs.append(df)
            except Exception as e:
                st.warning(f"Failed to read {uploaded_file.name}: {e}")
        if not dfs:
            st.error("❌ No valid files uploaded.")
        else:
            raw_df = pd.concat(dfs, ignore_index=True)
            st.subheader("📋 Raw Bugs (All Uploaded Files)")
            st.dataframe(raw_df, width='stretch')

            # allow user to pick date columns for detected and closed if present
            detected_col_guess, closed_col_guess = detect_date_columns(raw_df)
            cols_for_select = list(raw_df.columns)

            st.info("Map date columns (used for monthly aggregation and defect aging). If unsure, accept the defaults.")
            detected_choice = st.selectbox("Select Detected / Created date column", options=["(none)"] + cols_for_select, index=(cols_for_select.index(detected_col_guess)+1 if detected_col_guess in cols_for_select else 0))
            closed_choice = st.selectbox("Select Closed / Resolved date column", options=["(none)"] + cols_for_select, index=(cols_for_select.index(closed_col_guess)+1 if closed_col_guess in cols_for_select else 0))

            # normalize into canonical columns for downstream processing
            if detected_choice and detected_choice != "(none)":
                raw_df['created'] = pd.to_datetime(raw_df[detected_choice], errors='coerce')
            if closed_choice and closed_choice != "(none)":
                raw_df['resolutiondate'] = pd.to_datetime(raw_df[closed_choice], errors='coerce')

            # --- Validate required columns ---
            required_columns = ['Root Cause Category', 'Root Cause Description']
            missing_columns = [col for col in required_columns if col not in raw_df.columns]

            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
            else:
                # --- Add Defect Id if missing ---
                if 'Defect Id' not in raw_df.columns:
                    raw_df['Defect Id'] = [f"DEFECT-{i+1}" for i in range(len(raw_df))]

                if 'key' not in raw_df.columns:
                    raw_df['key'] = raw_df['Defect Id']

                if 'description' not in raw_df.columns:
                    raw_df['description'] = raw_df['Root Cause Description']

                if 'summary' not in raw_df.columns:
                    raw_df['summary'] = raw_df['Root Cause Category']

                # compute aging before metrics
                raw_df = compute_aging(raw_df)

                # --- Project-wise filter ---
                project_list = sorted(raw_df['Project'].unique())
                selected_projects = st.multiselect("Filter by Project", options=project_list, default=project_list)
                filtered_df = raw_df[raw_df['Project'].isin(selected_projects)]

                # --- Calculate Defect Accuracy ---
                total_defects = len(filtered_df)
                defect_count = filtered_df[filtered_df['Root Cause Category'] != 'Not a Defect'].shape[0]
                nota_defect_count = filtered_df[filtered_df['Root Cause Category'] == 'Not a Defect'].shape[0]
                defect_accuracy = (defect_count / total_defects) * 100 if total_defects > 0 else 0

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("📊 Total Defects", total_defects)
                with col2:
                    st.metric("✅ Valid Defects", defect_count)
                with col3:
                    st.metric("📈 Defect Accuracy", f"{defect_accuracy:.2f}%")
                with col4:
                    avg_aging = filtered_df['aging_days'].dropna().mean()
                    st.metric("⏳ Avg Defect Aging (days)", f"{avg_aging:.1f}" if pd.notna(avg_aging) else "N/A")

                # --- Preprocessing & Clustering ---
                bugs_list = filtered_df.to_dict(orient='records')
                descriptions, valid_bugs = preprocess_descriptions(bugs_list, desc_field='Root Cause Description', key_field='Defect Id', is_alm_manual=True)

                if not descriptions:
                    st.warning("❌ No valid descriptions found for clustering. Please check your files.")
                else:
                    clustered_bugs = cluster_defects(descriptions, valid_bugs, num_clusters=min(3, len(valid_bugs)))
                    df = pd.DataFrame(clustered_bugs)

                    # ensure aging present in df (from filtered_df)
                    if 'aging_days' not in df.columns and 'aging_days' in filtered_df.columns:
                        df = df.merge(filtered_df[['key', 'aging_days']], on='key', how='left')

                    # Store prepared DataFrame in session state so view persists across reruns
                    st.session_state['analysis_df'] = df
                    st.session_state['analysis_is_jira'] = False
                    st.session_state['analysis_source'] = 'manual_upload'
                    st.success(f"✅ Prepared {len(df)} defects for ALM analysis. Use the View selector below.")

# If an analysis DataFrame is stored in session_state, show the view selector and render accordingly
if 'analysis_df' in st.session_state and st.session_state.get('analysis_df') is not None:
    stored_df = st.session_state['analysis_df']
    stored_is_jira = st.session_state.get('analysis_is_jira', False)
    st.subheader("🔎 Analysis View")
    view_choice = st.radio("Choose View", ("Dashboard", "Detailed Defect Analysis"), index=0, horizontal=True, key='analysis_view')
    if view_choice == "Dashboard":
        display_dashboard(stored_df, is_jira_mode=stored_is_jira)
    else:
        display_bug_analysis(stored_df, is_jira_mode=stored_is_jira)

    if st.button("Clear Analysis"):
        for k in ['analysis_df', 'analysis_is_jira', 'analysis_source', 'analysis_view']:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()

