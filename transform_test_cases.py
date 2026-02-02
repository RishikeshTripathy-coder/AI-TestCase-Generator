
from typing import List, Dict, Any
import json

# -----------------------------
# Helper Functions
# -----------------------------
def transform_steps(steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform raw steps into structured steps."""
    return [
        {
            "Step Number": idx + 1,
            "Action": step.get("action", ""),
            "Data": step.get("data", ""),
            "Expected Result": step.get("expected_result", "")
        }
        for idx, step in enumerate(steps)
    ]


def transform_test_cases(raw_cases: str) -> List[Dict[str, Any]]:
    """Transform raw JSON string of test cases into structured test cases."""
    cleaned_cases = []
    for idx, case in enumerate(json.loads(raw_cases), 1):
        cleaned_cases.append({
            "Test Case ID": f"TC_{str(idx).zfill(3)}",
            "Title": case.get("title", ""),
            "Description": case.get("description", ""),
            "Steps": transform_steps(case.get("steps", []))
        })
    return cleaned_cases