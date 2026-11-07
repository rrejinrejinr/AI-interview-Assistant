import os
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Configurable Judge0 execution service endpoint
JUDGE0_URL = os.getenv("JUDGE0_URL", "http://localhost:2358").rstrip("/")
JUDGE0_API_KEY = os.getenv("JUDGE0_API_KEY", "")
JUDGE0_API_HOST = os.getenv("JUDGE0_API_HOST", "")

# Standard Judge0 Language IDs
LANGUAGE_ID_MAP = {
    "python": 71,       # Python (3.8.1)
    "py": 71,
    "javascript": 63,   # JavaScript (Node.js 12.14.0)
    "js": 63,
    "java": 62,         # Java (OpenJDK 13.0.1)
    "cpp": 54,          # C++ (GCC 9.2.0)
    "c++": 54,
    "c": 50             # C (GCC 9.2.0)
}

def get_judge0_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if JUDGE0_API_KEY:
        headers["X-RapidAPI-Key"] = JUDGE0_API_KEY
    if JUDGE0_API_HOST:
        headers["X-RapidAPI-Host"] = JUDGE0_API_HOST
    return headers

def check_judge0_health() -> Dict[str, Any]:
    """
    Checks whether Judge0 service is reachable.
    """
    try:
        url = f"{JUDGE0_URL}/about"
        res = requests.get(url, headers=get_judge0_headers(), timeout=3)
        if res.status_code == 200:
            return {"available": True, "details": res.json()}
        return {"available": False, "status_code": res.status_code}
    except Exception as e:
        logger.warning(f"Judge0 health check failed: {e}")
        return {"available": False, "error": str(e)}

def submit_code_judge0(
    source_code: str,
    language: str,
    stdin: str = "",
    expected_output: Optional[str] = None,
    cpu_time_limit: float = 5.0,
    memory_limit: int = 128000
) -> Dict[str, Any]:
    """
    Submits code to Judge0 for synchronous execution.
    """
    lang_key = language.strip().lower()
    lang_id = LANGUAGE_ID_MAP.get(lang_key, 71)

    payload = {
        "source_code": source_code,
        "language_id": lang_id,
        "stdin": stdin,
        "cpu_time_limit": cpu_time_limit,
        "memory_limit": memory_limit
    }
    if expected_output is not None:
        payload["expected_output"] = expected_output

    url = f"{JUDGE0_URL}/submissions?base64_encoded=false&wait=true"
    
    try:
        res = requests.post(url, json=payload, headers=get_judge0_headers(), timeout=10)
        if res.status_code in [200, 201]:
            data = res.json()
            status_obj = data.get("status", {})
            status_id = status_obj.get("id")
            status_desc = status_obj.get("description", "Unknown")

            stdout = (data.get("stdout") or "").rstrip()
            stderr = (data.get("stderr") or "").rstrip()
            compile_output = (data.get("compile_output") or "").rstrip()
            time_sec = float(data.get("time") or 0.0)
            memory_kb = int(data.get("memory") or 0)

            passed = False
            if status_id == 3: # Accepted
                passed = True
            elif expected_output is not None:
                passed = (stdout == expected_output.rstrip())

            return {
                "success": True,
                "passed": passed,
                "status_id": status_id,
                "status_description": status_desc,
                "stdout": stdout,
                "stderr": stderr,
                "compile_output": compile_output,
                "execution_time_ms": round(time_sec * 1000, 2),
                "memory_kb": memory_kb,
                "raw": data
            }
        else:
            return {
                "success": False,
                "error_type": "HTTP_ERROR",
                "status_code": res.status_code,
                "message": f"Judge0 returned status code {res.status_code}: {res.text}"
            }
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        logger.warning(f"Judge0 service unavailable: {e}")
        return {
            "success": False,
            "error_type": "SERVICE_UNAVAILABLE",
            "message": f"Judge0 execution service is unavailable at {JUDGE0_URL}. Please ensure your Judge0 Docker container is running.",
            "error_detail": str(e)
        }
    except Exception as e:
        logger.error(f"Error executing code via Judge0: {e}")
        return {
            "success": False,
            "error_type": "EXECUTION_EXCEPTION",
            "message": f"Unexpected error during code execution: {str(e)}"
        }

def evaluate_problem_submission(
    source_code: str,
    language: str,
    test_cases: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Runs a user submission against multiple problem test cases through Judge0.
    """
    if not test_cases:
        # If no test cases provided, execute once with empty input
        res = submit_code_judge0(source_code=source_code, language=language, stdin="")
        if not res.get("success"):
            return {
                "verdict": "Service Unavailable" if res.get("error_type") == "SERVICE_UNAVAILABLE" else "Execution Error",
                "passed": False,
                "passed_count": 0,
                "total_count": 0,
                "error_message": res.get("message"),
                "results": [res]
            }
        status_desc = res.get("status_description", "Completed")
        return {
            "verdict": status_desc,
            "passed": res.get("passed", False),
            "passed_count": 1 if res.get("passed") else 0,
            "total_count": 1,
            "results": [res]
        }

    results = []
    passed_count = 0
    primary_verdict = "Accepted"
    first_error_msg = None

    for idx, tc in enumerate(test_cases):
        inp = tc.get("input", "")
        exp = tc.get("expected_output", "")

        res = submit_code_judge0(
            source_code=source_code,
            language=language,
            stdin=inp,
            expected_output=exp
        )

        if not res.get("success"):
            # Judge0 unreachable or system error
            return {
                "verdict": "Service Unavailable" if res.get("error_type") == "SERVICE_UNAVAILABLE" else "Execution Error",
                "passed": False,
                "passed_count": passed_count,
                "total_count": len(test_cases),
                "error_message": res.get("message"),
                "results": results
            }

        status_desc = res.get("status_description", "Unknown")
        passed = res.get("passed", False)
        
        # If output matched
        actual_out = res.get("stdout", "")
        if exp and actual_out.strip() == exp.strip():
            passed = True
            res["passed"] = True

        if passed:
            passed_count += 1
        else:
            if primary_verdict == "Accepted":
                if "Compilation" in status_desc:
                    primary_verdict = "Compilation Error"
                elif "Time Limit" in status_desc:
                    primary_verdict = "Time Limit Exceeded"
                elif "Runtime" in status_desc:
                    primary_verdict = "Runtime Error"
                else:
                    primary_verdict = "Wrong Answer"

        results.append({
            "test_case_index": idx + 1,
            "input": inp,
            "expected_output": exp,
            "actual_output": actual_out,
            "passed": passed,
            "status_description": status_desc,
            "stderr": res.get("stderr"),
            "compile_output": res.get("compile_output"),
            "execution_time_ms": res.get("execution_time_ms", 0),
            "memory_kb": res.get("memory_kb", 0)
        })

    all_passed = (passed_count == len(test_cases))
    if not all_passed and primary_verdict == "Accepted":
        primary_verdict = "Wrong Answer"

    return {
        "verdict": primary_verdict if not all_passed else "Accepted",
        "passed": all_passed,
        "passed_count": passed_count,
        "total_count": len(test_cases),
        "results": results
    }
