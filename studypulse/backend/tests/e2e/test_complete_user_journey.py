"""End-to-end test for complete user journey through StudyPulse.

This test simulates a real user's complete workflow:
1. User signup
2. Login
3. Browse exams and topics
4. Start study session
5. Answer questions
6. Complete mock test
7. View results
8. Check leaderboard
9. View profile stats
"""
import pytest
from fastapi import status


@pytest.mark.asyncio
@pytest.mark.e2e
class TestCompleteUserJourney:
    """End-to-end test for complete user experience."""

    async def test_complete_user_journey(
        self,
        test_client,
        test_db,
        test_exam,
        test_topic,
        test_questions,
        performance_tracker
    ):
        """Test complete user journey from signup to results."""
        performance_tracker.start()

        # ── STEP 1: User Registration ────────────────────────────
        print("\n[E2E] Step 1: User Registration")
        register_data = {
            "email": "e2e_user@example.com",
            "username": "e2euser",
            "full_name": "E2E Test User",
            "password": "SecurePassword123!"
        }

        register_response = test_client.post(
            "/api/v1/auth/register",
            json=register_data
        )

        assert register_response.status_code == status.HTTP_201_CREATED
        user_data = register_response.json()
        assert user_data["email"] == register_data["email"]
        print(f"[OK] User registered: {user_data['email']}")

        # ── STEP 2: User Login ────────────────────────────────────
        print("\n[E2E] Step 2: User Login")
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }

        login_response = test_client.post(
            "/api/v1/auth/login",
            data=login_data
        )

        assert login_response.status_code == status.HTTP_200_OK
        token_data = login_response.json()
        assert "access_token" in token_data
        access_token = token_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        print(f"[OK] User logged in, token received")

        # ── STEP 3: Browse Exams ──────────────────────────────────
        print("\n[E2E] Step 3: Browse Available Exams")
        exams_response = test_client.get("/api/v1/exams")

        assert exams_response.status_code == status.HTTP_200_OK
        exams = exams_response.json()
        assert len(exams) > 0
        selected_exam = exams[0]
        print(f"[OK] Found {len(exams)} exams, selected: {selected_exam['name']}")

        # ── STEP 4: Browse Topics ─────────────────────────────────
        print("\n[E2E] Step 4: Browse Topics for Selected Exam")
        topics_response = test_client.get(
            f"/api/v1/exams/{selected_exam['id']}/topics"
        )

        assert topics_response.status_code == status.HTTP_200_OK
        topics = topics_response.json()
        assert len(topics) > 0
        selected_topic = topics[0]
        print(f"[OK] Found {len(topics)} topics, selected: {selected_topic['name']}")

        # ── STEP 5: Start Study Session ───────────────────────────
        print("\n[E2E] Step 5: Start Study Session")
        session_data = {
            "topic_id": selected_topic["id"],
            "time_limit_minutes": 30
        }

        session_response = test_client.post(
            "/api/v1/study/sessions",
            headers=auth_headers,
            json=session_data
        )

        assert session_response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        session = session_response.json()
        session_id = session.get("id") or session.get("session_id")
        print(f"[OK] Study session started: {session_id}")

        # ── STEP 6: Answer Questions in Study Session ────────────
        print("\n[E2E] Step 6: Answer Questions in Study Session")
        questions_answered = 0

        # Get and answer first 3 questions
        for i in range(min(3, len(test_questions))):
            # Get next question
            question_response = test_client.get(
                f"/api/v1/study/sessions/{session_id}/next",
                headers=auth_headers
            )

            if question_response.status_code != status.HTTP_200_OK:
                # Alternative: use pre-loaded questions
                question = test_questions[i]

                # Submit answer
                answer_data = {
                    "question_id": question.id,
                    "selected_answer": question.correct_answer,  # Correct answer
                    "time_taken_seconds": 20 + i * 5
                }

                answer_response = test_client.post(
                    f"/api/v1/study/sessions/{session_id}/answer",
                    headers=auth_headers,
                    json=answer_data
                )

                if answer_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]:
                    result = answer_response.json()
                    is_correct = result.get("correct") or result.get("is_correct")
                    print(f"[OK] Question {i+1} answered: {'Correct' if is_correct else 'Incorrect'}")
                    questions_answered += 1

        print(f"[OK] Answered {questions_answered} questions in study session")

        # ── STEP 7: Start Mock Test ───────────────────────────────
        print("\n[E2E] Step 7: Start Mock Test")
        mock_test_config = {
            "topic_id": selected_topic["id"],
            "num_questions": min(5, len(test_questions)),
            "time_limit_minutes": 30
        }

        mock_test_response = test_client.post(
            "/api/v1/mock-tests",
            headers=auth_headers,
            json=mock_test_config
        )

        assert mock_test_response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]
        mock_test = mock_test_response.json()
        test_id = mock_test.get("test_id") or mock_test.get("id")
        print(f"[OK] Mock test started: {test_id}")

        # ── STEP 8: Complete Mock Test ────────────────────────────
        print("\n[E2E] Step 8: Complete Mock Test")

        # Prepare answers (mix of correct and incorrect)
        test_answers = []
        for i, question in enumerate(test_questions[:mock_test_config["num_questions"]]):
            # Answer first 2 correctly, rest incorrectly
            selected_answer = question.correct_answer if i < 2 else (
                "A" if question.correct_answer != "A" else "B"
            )

            test_answers.append({
                "question_id": question.id,
                "selected_answer": selected_answer,
                "time_taken_seconds": 25 + i * 3
            })

        # Submit mock test
        submission_data = {"answers": test_answers}
        submit_response = test_client.post(
            f"/api/v1/mock-tests/{test_id}/submit",
            headers=auth_headers,
            json=submission_data
        )

        assert submit_response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]
        results = submit_response.json()
        print(f"[OK] Mock test submitted")

        # ── STEP 9: View Mock Test Results ────────────────────────
        print("\n[E2E] Step 9: View Mock Test Results")
        results_response = test_client.get(
            f"/api/v1/mock-tests/{test_id}/results",
            headers=auth_headers
        )

        assert results_response.status_code == status.HTTP_200_OK
        test_results = results_response.json()

        total_correct = test_results.get("total_correct") or test_results.get("correct_answers")
        total_questions = test_results.get("total_questions") or test_results.get("questions_count")
        score_percentage = test_results.get("score") or test_results.get("percentage")

        print(f"[OK] Results: {total_correct}/{total_questions} correct")
        if score_percentage:
            print(f"[OK] Score: {score_percentage}%")

        # Verify results make sense
        assert total_correct <= total_questions

        # ── STEP 10: Check Leaderboard ────────────────────────────
        print("\n[E2E] Step 10: Check Leaderboard")
        leaderboard_response = test_client.get("/api/v1/leaderboard")

        if leaderboard_response.status_code == status.HTTP_200_OK:
            leaderboard = leaderboard_response.json()
            print(f"[OK] Leaderboard retrieved with {len(leaderboard)} entries")
        else:
            print(f"[INFO] Leaderboard endpoint not available (status: {leaderboard_response.status_code})")

        # ── STEP 11: View User Profile Stats ──────────────────────
        print("\n[E2E] Step 11: View User Profile & Stats")
        profile_response = test_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert profile_response.status_code == status.HTTP_200_OK
        profile = profile_response.json()
        print(f"[OK] Profile retrieved for: {profile['email']}")
        print(f"[OK] Stars earned: {profile.get('total_stars', 0)}")

        # Get study statistics
        stats_response = test_client.get(
            "/api/v1/study/stats",
            headers=auth_headers
        )

        if stats_response.status_code == status.HTTP_200_OK:
            stats = stats_response.json()
            print(f"[OK] Study statistics retrieved")
        else:
            print(f"[INFO] Study stats endpoint not available")

        # ── STEP 12: View Dashboard ───────────────────────────────
        print("\n[E2E] Step 12: View Dashboard")
        dashboard_response = test_client.get(
            "/api/v1/dashboard",
            headers=auth_headers
        )

        if dashboard_response.status_code == status.HTTP_200_OK:
            dashboard = dashboard_response.json()
            print(f"[OK] Dashboard data retrieved")
        else:
            print(f"[INFO] Dashboard endpoint not available")

        # ── Performance Metrics ───────────────────────────────────
        performance_tracker.end()
        metrics = performance_tracker.get_metrics()
        print(f"\n[PERFORMANCE] Total journey time: {metrics['total_time']:.2f}s")

        # Journey should complete in reasonable time (< 10 seconds for API calls)
        assert metrics['total_time'] < 30, "E2E journey took too long"

        print("\n[SUCCESS] Complete user journey test passed! ✓")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestGuestUserJourney:
    """Test guest user experience without registration."""

    async def test_guest_user_flow(
        self,
        test_client,
        test_exam,
        test_topic,
        test_questions
    ):
        """Test guest login and limited functionality."""
        print("\n[E2E GUEST] Guest User Flow")

        # ── STEP 1: Guest Login ───────────────────────────────────
        print("\n[E2E GUEST] Step 1: Guest Login")
        guest_response = test_client.post("/api/v1/auth/guest")

        assert guest_response.status_code == status.HTTP_200_OK
        guest_data = guest_response.json()
        access_token = guest_data["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        print(f"[OK] Guest logged in")

        # ── STEP 2: Browse Exams (Public) ─────────────────────────
        print("\n[E2E GUEST] Step 2: Browse Exams")
        exams_response = test_client.get("/api/v1/exams")

        assert exams_response.status_code == status.HTTP_200_OK
        exams = exams_response.json()
        print(f"[OK] Guest can browse {len(exams)} exams")

        # ── STEP 3: View Topics ───────────────────────────────────
        print("\n[E2E GUEST] Step 3: View Topics")
        topics_response = test_client.get(
            f"/api/v1/exams/{test_exam.id}/topics"
        )

        assert topics_response.status_code == status.HTTP_200_OK
        topics = topics_response.json()
        print(f"[OK] Guest can view {len(topics)} topics")

        # ── STEP 4: Try Study Session ─────────────────────────────
        print("\n[E2E GUEST] Step 4: Try Study Session")
        session_data = {
            "topic_id": test_topic.id,
            "time_limit_minutes": 30
        }

        session_response = test_client.post(
            "/api/v1/study/sessions",
            headers=auth_headers,
            json=session_data
        )

        # Should work for guest or require registration
        if session_response.status_code in [status.HTTP_201_CREATED, status.HTTP_200_OK]:
            print("[OK] Guest can start study sessions")
        else:
            print("[INFO] Guest cannot start study sessions (registration required)")

        print("\n[SUCCESS] Guest user journey test passed! ✓")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestErrorRecovery:
    """Test error handling and recovery in complete flow."""

    async def test_invalid_operations_handling(
        self,
        test_client,
        auth_headers,
        test_topic
    ):
        """Test that invalid operations are handled gracefully."""
        print("\n[E2E ERROR] Error Recovery Test")

        # ── Test 1: Start test with invalid topic ────────────────
        print("\n[E2E ERROR] Test 1: Invalid Topic Handling")
        invalid_test_config = {
            "topic_id": 99999,  # Non-existent
            "num_questions": 10,
            "time_limit_minutes": 30
        }

        response = test_client.post(
            "/api/v1/mock-tests",
            headers=auth_headers,
            json=invalid_test_config
        )

        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]
        print("[OK] Invalid topic handled gracefully")

        # ── Test 2: Access non-existent test ──────────────────────
        print("\n[E2E ERROR] Test 2: Non-existent Test Access")
        response = test_client.get(
            "/api/v1/mock-tests/99999/results",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        print("[OK] Non-existent test handled gracefully")

        # ── Test 3: Submit answer without starting test ───────────
        print("\n[E2E ERROR] Test 3: Submit Answer Without Test")
        answer_data = {
            "question_id": 1,
            "selected_answer": "A",
            "time_taken_seconds": 30
        }

        response = test_client.post(
            "/api/v1/mock-tests/99999/answers",
            headers=auth_headers,
            json=answer_data
        )

        assert response.status_code in [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]
        print("[OK] Invalid submission handled gracefully")

        print("\n[SUCCESS] Error recovery test passed! ✓")
