#!/usr/bin/env python3
"""
StudyPulse Backend API Endpoint Tester
Tests all key endpoints on both localhost and Railway production
"""
import requests
import json
import time
from typing import Dict, List, Tuple
from urllib.parse import urlencode

def test_endpoint(method: str, url: str, headers: Dict = None, data: Dict = None, form_data: Dict = None) -> Dict:
    """Test a single endpoint and return results"""
    try:
        start_time = time.time()

        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method.upper() == "POST":
            if form_data:
                # Use form-encoded data for OAuth2 endpoints
                response = requests.post(url, headers=headers, data=form_data, timeout=10)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}

        elapsed_time = time.time() - start_time

        # Get response body
        try:
            response_body = response.json()
            body_str = json.dumps(response_body, indent=2)[:200]
        except:
            body_str = response.text[:200]

        return {
            "status_code": response.status_code,
            "response_time": round(elapsed_time, 3),
            "response_body": body_str,
            "full_response": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "error": None
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "full_response": None,
            "error": f"Connection Error: Cannot connect to server (is it running?)"
        }
    except requests.exceptions.Timeout as e:
        return {
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "full_response": None,
            "error": f"Timeout Error: Server took too long to respond"
        }
    except Exception as e:
        return {
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "full_response": None,
            "error": f"Error: {str(e)[:100]}"
        }

def test_all_endpoints(base_url: str, env_name: str):
    """Test all endpoints for a given environment"""
    results = []

    print(f"\n{'='*80}")
    print(f"Testing {env_name}: {base_url}")
    print(f"{'='*80}\n")

    # 1. Health Check
    print("1. Testing GET / (Health Check)")
    result = test_endpoint("GET", f"{base_url}/")
    results.append(("GET /", result))
    print(f"   Status: {result['status_code']}, Time: {result['response_time']}s")
    if result['error']:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Response: {result['response_body']}")
    print()

    # 2. List Exams
    print("2. Testing GET /api/v1/exams/ (List Exams)")
    result = test_endpoint("GET", f"{base_url}/api/v1/exams/")
    results.append(("GET /api/v1/exams/", result))
    print(f"   Status: {result['status_code']}, Time: {result['response_time']}s")
    if result['error']:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Response: {result['response_body']}")
    print()

    # 3. Guest Authentication
    print("3. Testing POST /api/v1/auth/guest (Guest Auth)")
    guest_data = {}
    result = test_endpoint("POST", f"{base_url}/api/v1/auth/guest",
                          headers={"Content-Type": "application/json"},
                          data=guest_data)
    results.append(("POST /api/v1/auth/guest", result))
    print(f"   Status: {result['status_code']}, Time: {result['response_time']}s")
    if result['error']:
        print(f"   Error: {result['error']}")
        guest_token = None
    else:
        print(f"   Response: {result['response_body']}")
        try:
            guest_token = result['full_response'].get('access_token')
            print(f"   Token obtained: {guest_token[:50] if guest_token else 'None'}...")
        except:
            guest_token = None
    print()

    # 4. Regular Login
    print("4. Testing POST /api/v1/auth/login (Regular Login)")
    login_form = {
        "username": "test@studypulse.com",
        "password": "password123"
    }
    result = test_endpoint("POST", f"{base_url}/api/v1/auth/login",
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          form_data=login_form)
    results.append(("POST /api/v1/auth/login", result))
    print(f"   Status: {result['status_code']}, Time: {result['response_time']}s")
    if result['error']:
        print(f"   Error: {result['error']}")
        auth_token = guest_token  # Fallback to guest token
    else:
        print(f"   Response: {result['response_body']}")
        try:
            auth_token = result['full_response'].get('access_token')
            print(f"   Token obtained: {auth_token[:50] if auth_token else 'None'}...")
        except:
            auth_token = guest_token  # Fallback to guest token
    print()

    # 5. Dashboard (needs auth)
    print("5. Testing GET /api/v1/dashboard (Dashboard Data)")
    if auth_token:
        result = test_endpoint("GET", f"{base_url}/api/v1/dashboard",
                              headers={
                                  "Content-Type": "application/json",
                                  "Authorization": f"Bearer {auth_token}"
                              })
    else:
        result = {
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "error": "No auth token available (previous auth failed)"
        }
    results.append(("GET /api/v1/dashboard", result))
    print(f"   Status: {result['status_code']}, Time: {result['response_time']}s")
    if result['error']:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Response: {result['response_body']}")
    print()

    # 6. Create Mock Test (needs auth)
    print("6. Testing POST /api/v1/mock-test/start (Create Mock Test)")
    if auth_token:
        mock_test_data = {
            "topic_id": 1,
            "question_count": 5,
            "previous_year_ratio": 0.7,
            "time_limit_seconds": 300
        }
        result = test_endpoint("POST", f"{base_url}/api/v1/mock-test/start",
                              headers={
                                  "Content-Type": "application/json",
                                  "Authorization": f"Bearer {auth_token}"
                              },
                              data=mock_test_data)
    else:
        result = {
            "status_code": None,
            "response_time": None,
            "response_body": None,
            "error": "No auth token available (previous auth failed)"
        }
    results.append(("POST /api/v1/mock-test/start", result))
    print(f"   Status: {result['status_code']}, Time: {result['response_time']}s")
    if result['error']:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Response: {result['response_body']}")
    print()

    return results

def print_summary_table(localhost_results: List, railway_results: List):
    """Print a summary table comparing localhost and Railway"""
    print("\n" + "="*100)
    print("SUMMARY TABLE")
    print("="*100)
    print(f"{'Endpoint':<35} {'Localhost':<30} {'Railway Production':<30}")
    print("-"*100)

    for i, (endpoint, localhost_result) in enumerate(localhost_results):
        railway_result = railway_results[i][1]

        # Format localhost status
        if localhost_result['error']:
            localhost_status = f"FAIL - {localhost_result['error'][:15]}"
        else:
            localhost_status = f"PASS ({localhost_result['status_code']}) - {localhost_result['response_time']}s"

        # Format railway status
        if railway_result['error']:
            railway_status = f"FAIL - {railway_result['error'][:15]}"
        else:
            railway_status = f"PASS ({railway_result['status_code']}) - {railway_result['response_time']}s"

        print(f"{endpoint:<35} {localhost_status:<30} {railway_status:<30}")

    print("="*100)

if __name__ == "__main__":
    # Test localhost
    localhost_results = test_all_endpoints("http://localhost:8001", "LOCALHOST")

    # Test Railway production
    railway_results = test_all_endpoints("https://askanand-simba.up.railway.app", "RAILWAY PRODUCTION")

    # Print summary
    print_summary_table(localhost_results, railway_results)
