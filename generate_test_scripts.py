# from dotenv import load_dotenv
# from light_client import LIGHTClient
# import os

# from utilities.prompts import BASE_PROMPT_2
# from utilities.prompts import BASE_PROMPT_3
# load_dotenv()

# USER = os.getenv("USER")
# MODEL = os.getenv("MODEL_NAME")
# client = LIGHTClient()


# CORTEX_BASE = "https://api.cortex.lilly.com"
# # GENERATOR_MODEL_NAME = f"{USER}-gherkin-generator-model"
# def generate_test_scripts(description, requirements, context=None):
#     print("\n 👉 Calling the function to generate test scripts")
#     PROMT = BASE_PROMPT_2
#     prompt = PROMT.format(description,requirements, context)
#     print("\nprompt:",prompt)
#     # headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     response = client.post(f"{CORTEX_BASE}/model/ask/{MODEL}", data={"q": prompt})
#     response.raise_for_status()
#     msg = response.json().get("message", "").strip()
#     if not msg:
#         raise ValueError("Model returned empty output.")
#     print(msg)
#     return msg
# def generate_test_scripts_from_manual_input(manual_input, context=None):
#     print("\n 👉 Calling the function to generate test scripts")
#     PROMT = BASE_PROMPT_3
#     prompt = PROMT.format(manual_input,context)
#     print("\nprompt:",prompt)
#     # headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     response = client.post(f"{CORTEX_BASE}/model/ask/{MODEL}", data={"q": prompt})
#     response.raise_for_status()
#     msg = response.json().get("message", "").strip()
#     if not msg:
#         raise ValueError("Model returned empty output.")
#     print(msg)
#     return msg

from dotenv import load_dotenv
from light_client import LIGHTClient
import os
import time

from utilities.prompts import BASE_PROMPT_2, BASE_PROMPT_3

load_dotenv()

USER = os.getenv("USER")
MODEL = os.getenv("MODEL_NAME")
client = LIGHTClient()

CORTEX_BASE = "https://api.cortex.lilly.com"


def call_cortex_with_retry(prompt, retries=3, delay=2):
    url = f"{CORTEX_BASE}/model/ask/{MODEL}"

    for attempt in range(1, retries + 1):
        try:
            print(f" Sending request to Cortex (Attempt {attempt})...")
            response = client.post(url, data={"q": prompt})

            # If 502, retry
            if response.status_code == 502:
                print(" 502 Bad Gateway — retrying...")
                time.sleep(delay)
                continue

            # Other errors -> raise
            response.raise_for_status()

            return response

        except Exception as e:
            print(f" Error: {e}")

            if attempt == retries:
                raise Exception(" Failed after max retries") from e

            time.sleep(delay)


def validate_testcases(requirement, context, draft):
    """
    Build a structured validation prompt, send it to the model and print a readable breakdown
    of each criterion so the operator can see why a particular score was assigned.
    """

    print("  Sending validation request to Cortex...")
    validation_prompt = f"""
You are a strict Test Case Validation Agent.

You will check EACH of these criteria and provide details:

1. ALIGNMENT - Are test cases aligned with the requirement?
2. CORRECTNESS - Are test cases technically correct?
3. COVERAGE - Do test cases cover all scenarios mentioned in requirement?
4. NO HALLUCINATIONS - Are there fabricated details not in requirement/context?
5. NO CONTRADICTIONS - Are there conflicting test cases?
6. EDGE CASES - Are edge cases and boundary conditions included?
7. COMPLETENESS - Are all test case fields complete (title, steps, expected results)?

Score from 0 to 5:
5 = Perfect (all criteria met excellently)
4 = Good (1-2 minor issues)
3 = Low quality (several issues)
2 = Incorrect (major issues)
1 = Contradicting (fundamentally wrong)
0 = Garbage output

Validate the following draft test cases:

Requirement:
{requirement}

Context:
{context}

Draft Test Cases:
{draft}

Respond ONLY in JSON with this EXACT structure:
{{
  "score": <0-5>,
  "alignment_check": {{ "passed": true/false, "details": "..." }},
  "correctness_check": {{ "passed": true/false, "details": "..." }},
  "coverage_check": {{ "passed": true/false, "details": "...", "scenarios_covered": ["..."], "missing_scenarios": ["..."] }},
  "hallucination_check": {{ "passed": true/false, "details": "..." }},
  "contradiction_check": {{ "passed": true/false, "details": "..." }},
  "edge_cases_check": {{ "passed": true/false, "details": "...", "edge_cases_found": ["..."] }},
  "completeness_check": {{ "passed": true/false, "details": "..." }},
  "overall_reasons": ["..."],
  "missing_points": ["..."],
  "is_requirement_aligned": true/false
}}
"""

    response = call_cortex_with_retry(validation_prompt)
    validation_raw = response.json().get("message", "").strip()

    if not validation_raw:
        print("  Validator returned empty response")
        return {"score": 0, "reasons": ["Empty response"], "missing_points": [], "is_requirement_aligned": False}

    try:
        import json
        validation = json.loads(validation_raw)
        score = validation.get("score", 0)

        print(f"\n  VALIDATION SCORE: {score}/5")
        print(" " + "="*70)

        # Check each criterion and print breakdown
        checks = [
            ("ALIGNMENT", validation.get("alignment_check")),
            ("CORRECTNESS", validation.get("correctness_check")),
            ("COVERAGE", validation.get("coverage_check")),
            ("HALLUCINATIONS", validation.get("hallucination_check")),
            ("CONTRADICTIONS", validation.get("contradiction_check")),
            ("EDGE CASES", validation.get("edge_cases_check")),
            ("COMPLETENESS", validation.get("completeness_check")),
        ]

        for check_name, check_data in checks:
            if not check_data:
                continue
            status = " PASS" if check_data.get("passed") else "❌ FAIL"
            details = check_data.get("details", "No details")
            print(f"\n {status} - {check_name}")
            print(f"   Details: {details}")

            if check_name == "COVERAGE":
                covered = check_data.get("scenarios_covered", [])
                missing = check_data.get("missing_scenarios", [])
                if covered:
                    print(f"   Covered: {covered}")
                if missing:
                    print(f"   Missing: {missing}")

            if check_name == "EDGE CASES":
                edge_cases = check_data.get("edge_cases_found", [])
                if edge_cases:
                    print(f"   Found: {edge_cases}")

        print("\n " + "="*70)

        # Overall assessment
        reasons = validation.get("overall_reasons", [])
        if reasons:
            print(f"\n Key Reasons for Score {score}:")
            for i, reason in enumerate(reasons, 1):
                print(f"   {i}. {reason}")

        missing = validation.get("missing_points", [])
        if missing:
            print(f"\n   Missing Points:")
            for i, point in enumerate(missing, 1):
                print(f"   {i}. {point}")

        aligned = validation.get("is_requirement_aligned", False)
        print(f"\n  Requirement Aligned: {'YES ' if aligned else 'NO '}")

        return validation
    except json.JSONDecodeError as e:
        print(f"  Failed to parse validator response: {e}")
        print(f"  Raw response: {validation_raw[:500]}")
        return {"score": 0, "reasons": ["Invalid JSON response"], "missing_points": [], "is_requirement_aligned": False}


def generate_test_scripts(description, requirements, context=None):
    print("\n 👉 Calling the function to generate test scripts")
    prompt = BASE_PROMPT_2.format(description, requirements, context)
    print("\nprompt:", prompt)

    response = call_cortex_with_retry(prompt)
    msg = response.json().get("message", "").strip()

    if not msg:
        raise ValueError("Model returned empty output.")

    print(msg)
    return msg


def generate_test_scripts_from_manual_input(manual_input, context=None):
    print("\n 👉 Calling the function to generate test scripts")
    prompt = BASE_PROMPT_3.format(manual_input, context)
    print("\nprompt:", prompt)

    response = call_cortex_with_retry(prompt)
    msg = response.json().get("message", "").strip()

    if not msg:
        raise ValueError("Model returned empty output.")

    print(msg)
    return msg
