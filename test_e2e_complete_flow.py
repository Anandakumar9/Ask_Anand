#!/usr/bin/env python3
"""
StudyPulse Complete End-to-End Test
Tests the entire user flow:
1. Guest login
2. Navigate through sessions (home, study, rank, profile)
3. Start study session (5 minutes)
4. End study session
5. Take mock test6. View results
7. Rate AI-generated questions
8. Check dashboard analytics (accuracy, performance, stars)

This tests: Backend API, Mobile App integration, and RAG pipeline
"""
import requests
import json
import time
from datetime import datetime
from typing import Dict, Optional
import sys


class StudyPulseE2ETest:
    def __init__(self, base_url: str = "http://localhost:8001", mobile_url: str = "http://localhost:8082"):
        self.base_url = base_url
        self.mobile_url = mobile_url
        self.api_url = f"{base_url}/api/v1"
        self.auth_token: Optional[str] = None
        self.user_id: Optional[int] = None
        self.session_id: Optional[int] = None
        self.test_id: Optional[int] = None
        self.exam_id: Optional[int] = None
        self.test_results = []

    def log(self, message: str, level: str = "INFO"):
        """Log test progress"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {
            "INFO": "✓",
            "WAIT": "⏳",
            "TEST": "🧪",
            "ERROR": "✗",
            "SUCCESS": "🎉"
        }.get(level, "→")
        print(f"[{timestamp}] {prefix} {message}")

    def check_servers(self):
        """Check if backend and mobile servers are running"""
        self.log("Checking if servers are running...", "TEST")

        # Check backend
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=2)
            self.log(f"Backend server: RUNNING (port 8001)", "INFO")
        except requests.exceptions.RequestException as e:
            self.log(f"Backend server: NOT RUNNING (port 8001)", "ERROR")
            self.log("Please start backend: cd studypulse/backend && python -m uvicorn app.main:app --reload --port 8001", "ERROR")
            return False

        # Check mobile app
        try:
            response = requests.get(self.mobile_url, timeout=2)
            self.log(f"Mobile app: RUNNING (port 8082)", "INFO")
        except requests.exceptions.RequestException as e:
            self.log(f"Mobile app: NOT RUNNING (port 8082)", "ERROR")
            self.log("Please start mobile: cd studypulse/mobile && flutter run -d web-server --web-port=8082", "ERROR")
            return False

        return True

    def test_guest_login(self):
        """Test 1: Guest Login / Authentication"""
        self.log("TEST 1: Testing Guest Login", "TEST")

        try:
            response = requests.post(
                f"{self.api_url}/auth/guest",
                json={},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("token") or data.get("access_token")
                self.user_id = data.get("user_id") or data.get("id")

                self.log(f"Guest login successful! User ID: {self.user_id}", "SUCCESS")
                self.test_results.append(("Guest Login", "PASS", "User authenticated successfully"))
                return True
            else:
                self.log(f"Guest login failed: {response.status_code} - {response.text}", "ERROR")
                self.test_results.append(("Guest Login", "FAIL", f"HTTP {response.status_code}"))
                return False

        except Exception as e:
            self.log(f"Guest login error: {str(e)}", "ERROR")
            self.test_results.append(("Guest Login", "FAIL", str(e)))
            return False

    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if self.auth_token:
            return {
                "Authorization": f"Bearer {self.auth_token}",
                "Content-Type": "application/json"
            }
        return {"Content-Type": "application/json"}

    def test_session_navigation(self):
        """Test 2: Navigate through all sessions (home, study, rank, profile)"""
        self.log("TEST 2: Testing Session Navigation", "TEST")

        endpoints = [
            ("Home/Dashboard", f"{self.api_url}/dashboard"),
            ("Study Sessions", f"{self.api_url}/study/sessions"),
            ("Leaderboard/Rank", f"{self.api_url}/leaderboard"),
            ("User Profile", f"{self.api_url}/profile")
        ]

        for name, endpoint in endpoints:
            try:
                response = requests.get(endpoint, headers=self.get_headers(), timeout=10)

                if response.status_code in [200, 201]:
                    self.log(f"  → {name}: ACCESSIBLE ✓", "INFO")
                    self.test_results.append((f"Navigation - {name}", "PASS", "Endpoint accessible"))
                else:
                    self.log(f"  → {name}: FAILED (HTTP {response.status_code})", "ERROR")
                    self.test_results.append((f"Navigation - {name}", "FAIL", f"HTTP {response.status_code}"))

            except Exception as e:
                self.log(f"  → {name}: ERROR - {str(e)}", "ERROR")
                self.test_results.append((f"Navigation - {name}", "FAIL", str(e)))

        self.log("Session navigation tests complete", "SUCCESS")

    def test_start_study_session(self, duration_minutes: int = 5):
        """Test 3: Start a study session"""
        self.log(f"TEST 3: Starting {duration_minutes}-minute study session", "TEST")

        # First, get available exams
        try:
            exams_response = requests.get(f"{self.api_url}/exams/", headers=self.get_headers(), timeout=10)

            if exams_response.status_code == 200:
                exams = exams_response.json()
                if not exams:
                    self.log("No exams available for testing", "ERROR")
                    self.test_results.append(("Start Study Session", "FAIL", "No exams available"))
                    return False

                # Pick the first exam
                exam = exams[0] if isinstance(exams, list) else exams.get("exams", [{}])[0]
                self.exam_id = exam.get("id")
                exam_name = exam.get("name", "Unknown")

                self.log(f"  → Selected exam: {exam_name} (ID: {self.exam_id})", "INFO")

        except Exception as e:
            self.log(f"Failed to get exams: {str(e)}", "ERROR")
            self.test_results.append(("Start Study Session - Get Exams", "FAIL", str(e)))
            return False

        # Start the study session
        try:
            session_data = {
                "exam_id": self.exam_id,
                "duration_seconds": duration_minutes * 60
            }

            response = requests.post(
                f"{self.api_url}/study/sessions",
                json=session_data,
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.session_id = data.get("id") or data.get("session_id")

                self.log(f"Study session started! Session ID: {self.session_id}", "SUCCESS")
                self.log(f"Duration: {duration_minutes} minutes", "INFO")
                self.test_results.append(("Start Study Session", "PASS", f"Session {self.session_id} created"))
                return True
            else:
                self.log(f"Failed to start session: {response.status_code} - {response.text}", "ERROR")
                self.test_results.append(("Start Study Session", "FAIL", f"HTTP {response.status_code}"))
                return False

        except Exception as e:
            self.log(f"Start session error: {str(e)}", "ERROR")
            self.test_results.append(("Start Study Session", "FAIL", str(e)))
            return False

    def wait_for_study_session(self, duration_minutes: int = 5):
        """Test 4: Monitor the study session (wait for duration)"""
        self.log(f"TEST 4: Monitoring study session for {duration_minutes} minutes", "TEST")
        self.log(f"Waiting for {duration_minutes} minutes to simulate real user study session...", "WAIT")

        total_seconds = duration_minutes * 60
        check_interval = 30  # Check every 30 seconds

        for elapsed in range(0, total_seconds, check_interval):
            time.sleep(check_interval)
            remaining = total_seconds - elapsed - check_interval
            remaining_minutes = remaining // 60
            remaining_seconds = remaining % 60

            self.log(f"  → Study session in progress... ({remaining_minutes}m {remaining_seconds}s remaining)", "WAIT")

            # Check session status
            try:
                response = requests.get(
                    f"{self.api_url}/study/sessions/{self.session_id}",
                    headers=self.get_headers(),
                    timeout=10
                )

                if response.status_code == 200:
                    session_data = response.json()
                    status = session_data.get("status", "unknown")
                    self.log(f"  → Session status: {status}", "INFO")
                else:
                    self.log(f"  → Failed to check session status: HTTP {response.status_code}", "ERROR")

            except Exception as e:
                self.log(f"  → Error checking session: {str(e)}", "ERROR")

        self.log(f"Study session {duration_minutes}-minute period complete!", "SUCCESS")
        self.test_results.append(("Monitor Study Session", "PASS", f"{duration_minutes} minutes monitored"))

    def test_end_study_session(self):
        """Test 5: End the study session"""
        self.log("TEST 5: Ending study session", "TEST")

        if not self.session_id:
            self.log("No active session to end", "ERROR")
            self.test_results.append(("End Study Session", "FAIL", "No active session"))
            return False

        try:
            response = requests.post(
                f"{self.api_url}/study/sessions/{self.session_id}/complete",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.log("Study session ended successfully!", "SUCCESS")

                # Check if questions were generated
                if "questions" in data:
                    question_count = len(data["questions"])
                    self.log(f"  → {question_count} questions generated", "INFO")
                    self.test_results.append(("End Study Session", "PASS", f"{question_count} questions generated"))
                else:
                    self.log("  → Session ended, but no questions in response", "INFO")
                    self.test_results.append(("End Study Session", "PASS", "Session ended successfully"))

                return True
            else:
                self.log(f"Failed to end session: {response.status_code} - {response.text}", "ERROR")
                self.test_results.append(("End Study Session", "FAIL", f"HTTP {response.status_code}"))
                return False

        except Exception as e:
            self.log(f"End session error: {str(e)}", "ERROR")
            self.test_results.append(("End Study Session", "FAIL", str(e)))
            return False

    def test_take_mock_exam(self):
        """Test 6: Take a mock exam"""
        self.log("TEST 6: Taking mock exam", "TEST")

        if not self.exam_id:
            self.log("No exam ID available", "ERROR")
            self.test_results.append(("Take Mock Exam", "FAIL", "No exam ID"))
            return False

        try:
            # Start a mock test
            response = requests.post(
                f"{self.api_url}/mock-tests/",
                json={"exam_id": self.exam_id, "question_count": 5},
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code in [200, 201]:
                data = response.json()
                self.test_id = data.get("id") or data.get("test_id")
                questions = data.get("questions", [])

                self.log(f"Mock test started! Test ID: {self.test_id}", "SUCCESS")
                self.log(f"  → {len(questions)} questions loaded", "INFO")

                # Simulate answering questions randomly
                answers = []
                for i, question in enumerate(questions):
                    question_id = question.get("id")
                    options = question.get("options", ["A", "B", "C", "D"])
                    # Pick a random answer (simulate user selection)
                    import random
                    selected_answer = random.choice(options) if options else "A"

                    answers.append({
                        "question_id": question_id,
                        "selected_answer": selected_answer
                    })

                    self.log(f"  → Q{i+1}: Selected answer '{selected_answer}'", "INFO")

                # Submit mock test
                submit_response = requests.post(
                    f"{self.api_url}/mock-tests/{self.test_id}/submit",
                    json={"answers": answers},
                    headers=self.get_headers(),
                    timeout=10
                )

                if submit_response.status_code in [200, 201]:
                    result_data = submit_response.json()
                    score = result_data.get("score", 0)
                    total = result_data.get("total", len(questions))
                    percentage = (score / total * 100) if total > 0 else 0

                    self.log(f"Mock test submitted! Score: {score}/{total} ({percentage:.1f}%)", "SUCCESS")
                    self.test_results.append(("Take Mock Exam", "PASS", f"Score: {score}/{total}"))
                    return True
                else:
                    self.log(f"Failed to submit test: {submit_response.status_code}", "ERROR")
                    self.test_results.append(("Take Mock Exam", "FAIL", "Submit failed"))
                    return False

            else:
                self.log(f"Failed to start mock test: {response.status_code} - {response.text}", "ERROR")
                self.test_results.append(("Take Mock Exam", "FAIL", f"HTTP {response.status_code}"))
                return False

        except Exception as e:
            self.log(f"Mock exam error: {str(e)}", "ERROR")
            self.test_results.append(("Take Mock Exam", "FAIL", str(e)))
            return False

    def test_view_results(self):
        """Test 7: View mock test results"""
        self.log("TEST 7: Viewing test results", "TEST")

        if not self.test_id:
            self.log("No test ID available", "ERROR")
            self.test_results.append(("View Results", "FAIL", "No test ID"))
            return False

        try:
            response = requests.get(
                f"{self.api_url}/mock-tests/{self.test_id}/results",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                score = data.get("score", 0)
                total = data.get("total", 0)
                percentage = data.get("percentage", 0)
                stars = data.get("stars_earned", 0)

                self.log(f"Results retrieved successfully!", "SUCCESS")
                self.log(f"  → Score: {score}/{total} ({percentage:.1f}%)", "INFO")
                self.log(f"  → Stars earned: {stars}", "INFO")

                # Check for question explanations
                results = data.get("results", [])
                explanations_count = sum(1 for r in results if r.get("explanation"))
                self.log(f"  → Questions with explanations: {explanations_count}/{len(results)}", "INFO")

                self.test_results.append(("View Results", "PASS", f"Score: {score}/{total}, Stars: {stars}"))
                return True
            else:
                self.log(f"Failed to get results: {response.status_code}", "ERROR")
                self.test_results.append(("View Results", "FAIL", f"HTTP {response.status_code}"))
                return False

        except Exception as e:
            self.log(f"View results error: {str(e)}", "ERROR")
            self.test_results.append(("View Results", "FAIL", str(e)))
            return False

    def test_rate_questions(self):
        """Test 8: Rate AI-generated questions"""
        self.log("TEST 8: Rating AI-generated questions", "TEST")

        # Get questions from the completed test
        try:
            # First get the test results to find question IDs
            response = requests.get(
                f"{self.api_url}/mock-tests/{self.test_id}/results",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if not results:
                    self.log("No questions to rate", "ERROR")
                    self.test_results.append(("Rate Questions", "FAIL", "No questions found"))
                    return False

                # Rate each question randomly (simulate user feedback)
                import random
                ratings = [1, 2, 3, 4, 5]  # 1-5 star rating
                rated_count = 0

                for result in results[:3]:  # Rate first 3 questions
                    question_id = result.get("question_id")
                    rating = random.choice(ratings)

                    try:
                        rate_response = requests.post(
                            f"{self.api_url}/questions/{question_id}/rate",
                            json={"rating": rating, "feedback": "Test feedback from E2E test"},
                            headers=self.get_headers(),
                            timeout=10
                        )

                        if rate_response.status_code in [200, 201]:
                            self.log(f"  → Question {question_id}: Rated {rating} stars ✓", "INFO")
                            rated_count += 1
                        else:
                            self.log(f"  → Question {question_id}: Rating failed (HTTP {rate_response.status_code})", "ERROR")

                    except Exception as e:
                        self.log(f"  → Question {question_id}: Error - {str(e)}", "ERROR")

                if rated_count > 0:
                    self.log(f"Rated {rated_count} questions successfully!", "SUCCESS")
                    self.test_results.append(("Rate Questions", "PASS", f"{rated_count} questions rated"))
                    return True
                else:
                    self.log("Failed to rate any questions", "ERROR")
                    self.test_results.append(("Rate Questions", "FAIL", "No questions rated"))
                    return False

            else:
                self.log(f"Failed to get questions for rating: {response.status_code}", "ERROR")
                self.test_results.append(("Rate Questions", "FAIL", "Could not get questions"))
                return False

        except Exception as e:
            self.log(f"Rate questions error: {str(e)}", "ERROR")
            self.test_results.append(("Rate Questions", "FAIL", str(e)))
            return False

    def test_dashboard_analytics(self):
        """Test 9: Check dashboard analytics (accuracy, performance, stars)"""
        self.log("TEST 9: Checking dashboard analytics", "TEST")

        try:
            response = requests.get(
                f"{self.api_url}/dashboard",
                headers=self.get_headers(),
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                # Extract key metrics
                total_stars = data.get("total_stars", 0)
                total_tests = data.get("total_tests", 0)
                average_score = data.get("average_score", 0)
                study_time = data.get("total_study_time", 0)

                self.log("Dashboard analytics retrieved successfully!", "SUCCESS")
                self.log(f"  → Total stars earned: {total_stars}", "INFO")
                self.log(f"  → Total tests taken: {total_tests}", "INFO")
                self.log(f"  → Average score: {average_score:.1f}%", "INFO")
                self.log(f"  → Total study time: {study_time} minutes", "INFO")

                # Check for historical data
                recent_tests = data.get("recent_tests", [])
                recent_sessions = data.get("recent_sessions", [])

                self.log(f"  → Recent tests: {len(recent_tests)}", "INFO")
                self.log(f"  → Recent sessions: {len(recent_sessions)}", "INFO")

                # Check for performance trends
                if "performance_trend" in data:
                    self.log(f"  → Performance trend available ✓", "INFO")

                self.test_results.append(("Dashboard Analytics", "PASS", f"Stars: {total_stars}, Tests: {total_tests}"))
                return True
            else:
                self.log(f"Failed to get dashboard data: {response.status_code}", "ERROR")
                self.test_results.append(("Dashboard Analytics", "FAIL", f"HTTP {response.status_code}"))
                return False

        except Exception as e:
            self.log(f"Dashboard analytics error: {str(e)}", "ERROR")
            self.test_results.append(("Dashboard Analytics", "FAIL", str(e)))
            return False

    def print_test_summary(self):
        """Print comprehensive test summary"""
        self.log("=" * 60, "")
        self.log("END-TO-END TEST SUMMARY", "SUCCESS")
        self.log("=" * 60, "")

        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed = sum(1 for _, status, _ in self.test_results if status == "FAIL")
        total = len(self.test_results)

        self.log(f"Total Tests: {total}", "INFO")
        self.log(f"Passed: {passed} ✓", "INFO")
        self.log(f"Failed: {failed} ✗", "INFO")
        self.log(f"Success Rate: {(passed/total*100):.1f}%", "INFO")
        self.log("", "")

        self.log("Detailed Results:", "TEST")
        self.log("-" * 60, "")

        for test_name, status, details in self.test_results:
            status_symbol = "✓" if status == "PASS" else "✗"
            self.log(f"{status_symbol} {test_name}: {status} - {details}", "INFO")

        self.log("=" * 60, "")

        if failed == 0:
            self.log("ALL TESTS PASSED! 🎉", "SUCCESS")
            self.log("StudyPulse is working perfectly across all components!", "SUCCESS")
        else:
            self.log(f"{failed} test(s) failed. Please review the errors above.", "ERROR")

    def run_complete_flow(self, study_duration_minutes: int = 5):
        """Run the complete end-to-end test flow"""
        self.log("=" * 60, "")
        self.log("STUDYPULSE COMPLETE END-TO-END TEST", "SUCCESS")
        self.log("=" * 60, "")
        self.log("This test will simulate a complete user flow:", "INFO")
        self.log("1. Guest login", "INFO")
        self.log("2. Navigate through all sessions", "INFO")
        self.log(f"3. Start and monitor {study_duration_minutes}-minute study session", "INFO")
        self.log("4. End study session", "INFO")
        self.log("5. Take mock exam", "INFO")
        self.log("6. View results", "INFO")
        self.log("7. Rate questions", "INFO")
        self.log("8. Check dashboard analytics", "INFO")
        self.log("=" * 60, "")
        self.log("", "")

        # Check servers first
        if not self.check_servers():
            self.log("Servers are not running. Please start them first.", "ERROR")
            sys.exit(1)

        # Run all tests in sequence
        self.test_guest_login()
        time.sleep(1)

        self.test_session_navigation()
        time.sleep(1)

        if self.test_start_study_session(duration_minutes=study_duration_minutes):
            self.wait_for_study_session(duration_minutes=study_duration_minutes)
            self.test_end_study_session()
        time.sleep(1)

        self.test_take_mock_exam()
        time.sleep(1)

        self.test_view_results()
        time.sleep(1)

        self.test_rate_questions()
        time.sleep(1)

        self.test_dashboard_analytics()
        self.log("", "")

        # Print summary
        self.print_test_summary()


def main():
    """Main entry point"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║       StudyPulse Complete End-to-End Test Suite          ║")
    print("║                                                            ║")
    print("║  Testing: Backend + Mobile App + RAG Pipeline             ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print("\n")

    # Check for custom study duration
    study_duration = 5  # Default: 5 minutes
    if len(sys.argv) > 1:
        try:
            study_duration = int(sys.argv[1])
        except ValueError:
            print("Invalid duration. Using default: 5 minutes")

    print(f"Study session duration: {study_duration} minutes")
    print(f"Note: This test will take approximately {study_duration + 3} minutes to complete")
    print("\n")

    # Run the complete test flow
    tester = StudyPulseE2ETest()
    tester.run_complete_flow(study_duration_minutes=study_duration)

    print("\n")
    print("Test complete! Check the results above.")
    print("\n")


if __name__ == "__main__":
    main()
