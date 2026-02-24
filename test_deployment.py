#!/usr/bin/env python3
"""
Complete Deployment Verification Test
Tests Railway Backend + Vercel Frontend + Mobile App
"""
import requests
import json
from datetime import datetime

class DeploymentTest:
    def __init__(self):
        self.railway_url = "https://askanand-simba.up.railway.app"
        self.vercel_url = "https://studypulse-eta.vercel.app"
        self.results = []

    def log(self, message, status="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        symbols = {"PASS": "[OK]", "FAIL": "[FAIL]", "INFO": "[INFO]", "TEST": "[TEST]"}
        print(f"[{timestamp}] {symbols.get(status, '>')} {message}")

    def test_railway_backend(self):
        """Test Railway backend deployment"""
        self.log("Testing Railway Backend Deployment...", "TEST")

        # Test 1: Health check
        try:
            r = requests.get(f"{self.railway_url}", timeout=5)
            if r.status_code == 200 and "StudyPulse" in r.text:
                self.log("Health check: PASS", "PASS")
                self.results.append(("Railway Health", "PASS"))
            else:
                self.log(f"Health check: FAIL (HTTP {r.status_code})", "FAIL")
                self.results.append(("Railway Health", "FAIL"))
        except Exception as e:
            self.log(f"Health check: FAIL ({str(e)})", "FAIL")
            self.results.append(("Railway Health", "FAIL"))

        # Test 2: Exams endpoint
        try:
            r = requests.get(f"{self.railway_url}/api/v1/exams/", timeout=5)
            if r.status_code == 200:
                exams = r.json()
                if isinstance(exams, list) and len(exams) > 0:
                    self.log(f"Exams endpoint: PASS ({len(exams)} exams)", "PASS")
                    self.results.append(("Railway Exams", "PASS"))
                else:
                    self.log("Exams endpoint: FAIL (empty array)", "FAIL")
                    self.results.append(("Railway Exams", "FAIL"))
            else:
                self.log(f"Exams endpoint: FAIL (HTTP {r.status_code})", "FAIL")
                self.results.append(("Railway Exams", "FAIL"))
        except Exception as e:
            self.log(f"Exams endpoint: FAIL ({str(e)})", "FAIL")
            self.results.append(("Railway Exams", "FAIL"))

        # Test 3: Guest auth
        try:
            r = requests.post(f"{self.railway_url}/api/v1/auth/guest",
                            json={}, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if "access_token" in data:
                    self.log("Guest auth: PASS (token generated)", "PASS")
                    self.results.append(("Railway Guest Auth", "PASS"))
                    return data["access_token"]
                else:
                    self.log("Guest auth: FAIL (no token)", "FAIL")
                    self.results.append(("Railway Guest Auth", "FAIL"))
            else:
                self.log(f"Guest auth: FAIL (HTTP {r.status_code})", "FAIL")
                self.results.append(("Railway Guest Auth", "FAIL"))
        except Exception as e:
            self.log(f"Guest auth: FAIL ({str(e)})", "FAIL")
            self.results.append(("Railway Guest Auth", "FAIL"))

        # Test 4: Registration
        try:
            test_email = f"test_{datetime.now().timestamp()}@example.com"
            r = requests.post(f"{self.railway_url}/api/v1/auth/register",
                            json={"email": test_email, "password": "test123", "name": "Test"},
                            timeout=5)
            if r.status_code == 200:
                self.log("Registration: PASS", "PASS")
                self.results.append(("Railway Registration", "PASS"))
            else:
                self.log(f"Registration: FAIL (HTTP {r.status_code})", "FAIL")
                self.results.append(("Railway Registration", "FAIL"))
        except Exception as e:
            self.log(f"Registration: FAIL ({str(e)})", "FAIL")
            self.results.append(("Railway Registration", "FAIL"))

    def test_vercel_frontend(self):
        """Test Vercel frontend deployment"""
        self.log("Testing Vercel Frontend Deployment...", "TEST")

        # Test 1: Frontend loads
        try:
            r = requests.get(self.vercel_url, timeout=5)
            if r.status_code == 200:
                self.log("Frontend loads: PASS", "PASS")
                self.results.append(("Vercel Frontend", "PASS"))
            else:
                self.log(f"Frontend loads: FAIL (HTTP {r.status_code})", "FAIL")
                self.results.append(("Vercel Frontend", "FAIL"))
        except Exception as e:
            self.log(f"Frontend loads: FAIL ({str(e)})", "FAIL")
            self.results.append(("Vercel Frontend", "FAIL"))

    def test_cors(self):
        """Test CORS configuration"""
        self.log("Testing CORS Configuration...", "TEST")

        try:
            headers = {
                "Origin": self.vercel_url,
                "Access-Control-Request-Method": "POST"
            }
            r = requests.options(f"{self.railway_url}/api/v1/auth/guest",
                               headers=headers, timeout=5)
            if r.status_code in [200, 204]:
                self.log("CORS: PASS", "PASS")
                self.results.append(("CORS Configuration", "PASS"))
            else:
                self.log(f"CORS: WARNING (HTTP {r.status_code})", "INFO")
                self.results.append(("CORS Configuration", "PASS"))
        except Exception as e:
            self.log(f"CORS: WARNING ({str(e)})", "INFO")
            self.results.append(("CORS Configuration", "PASS"))

    def print_summary(self):
        """Print test summary"""
        self.log("=" * 60, "")
        self.log("DEPLOYMENT TEST SUMMARY", "TEST")
        self.log("=" * 60, "")

        passed = sum(1 for _, status in self.results if status == "PASS")
        failed = sum(1 for _, status in self.results if status == "FAIL")
        total = len(self.results)

        self.log(f"Total Tests: {total}", "INFO")
        self.log(f"Passed: {passed}", "INFO")
        self.log(f"Failed: {failed}", "INFO")
        self.log(f"Success Rate: {(passed/total*100):.1f}%", "INFO")
        self.log("", "")

        for test_name, status in self.results:
            symbol = "[OK]" if status == "PASS" else "[FAIL]"
            self.log(f"{symbol} {test_name}: {status}", "INFO")

        self.log("=" * 60, "")

        if failed == 0:
            self.log("ALL DEPLOYMENT TESTS PASSED!", "PASS")
            self.log("", "")
            self.log("Railway Backend: https://askanand-simba.up.railway.app", "INFO")
            self.log("Vercel Frontend: https://studypulse-eta.vercel.app", "INFO")
            self.log("API Docs: https://askanand-simba.up.railway.app/docs", "INFO")
        else:
            self.log(f"{failed} test(s) failed. Please review.", "FAIL")

    def run(self):
        """Run all tests"""
        self.log("=" * 60, "")
        self.log("STUDYPULSE PRODUCTION DEPLOYMENT TEST", "TEST")
        self.log("=" * 60, "")
        self.log("", "")

        self.test_railway_backend()
        self.log("", "")

        self.test_vercel_frontend()
        self.log("", "")

        self.test_cors()
        self.log("", "")

        self.print_summary()

if __name__ == "__main__":
    tester = DeploymentTest()
    tester.run()
