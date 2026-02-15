"""Load testing for StudyPulse API with concurrent users.

Tests API performance under realistic load scenarios:
- 100 concurrent users
- Mixed read/write operations
- Realistic user behavior patterns
"""
import asyncio
import time
from typing import List, Dict
import statistics

import pytest
import httpx


@pytest.mark.load
@pytest.mark.asyncio
class TestConcurrentUsers:
    """Test API performance with multiple concurrent users."""

    async def simulate_user_session(
        self,
        user_id: int,
        base_url: str,
        topic_id: int,
        metrics: List[Dict]
    ):
        """Simulate a single user's session."""
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            session_metrics = {
                "user_id": user_id,
                "operations": [],
                "errors": 0,
                "total_time": 0
            }

            start_time = time.time()

            try:
                # 1. Guest login
                op_start = time.time()
                response = await client.post("/api/v1/auth/guest")
                session_metrics["operations"].append({
                    "operation": "guest_login",
                    "status": response.status_code,
                    "time": time.time() - op_start
                })

                if response.status_code != 200:
                    session_metrics["errors"] += 1
                    return

                token = response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # 2. Get exams
                op_start = time.time()
                response = await client.get("/api/v1/exams")
                session_metrics["operations"].append({
                    "operation": "get_exams",
                    "status": response.status_code,
                    "time": time.time() - op_start
                })

                if response.status_code != 200:
                    session_metrics["errors"] += 1

                # 3. Start study session
                op_start = time.time()
                response = await client.post(
                    "/api/v1/study/sessions",
                    headers=headers,
                    json={"topic_id": topic_id, "time_limit_minutes": 30}
                )
                session_metrics["operations"].append({
                    "operation": "start_session",
                    "status": response.status_code,
                    "time": time.time() - op_start
                })

                # 4. Small delay to simulate reading
                await asyncio.sleep(0.5)

                # 5. Get user profile
                op_start = time.time()
                response = await client.get("/api/v1/auth/me", headers=headers)
                session_metrics["operations"].append({
                    "operation": "get_profile",
                    "status": response.status_code,
                    "time": time.time() - op_start
                })

            except Exception as e:
                session_metrics["errors"] += 1
                session_metrics["error_message"] = str(e)

            session_metrics["total_time"] = time.time() - start_time
            metrics.append(session_metrics)

    async def test_100_concurrent_users(self, test_client, test_topic):
        """Test with 100 concurrent users."""
        print("\n[LOAD TEST] Starting 100 concurrent users test...")

        base_url = "http://testserver"
        num_users = 100
        metrics: List[Dict] = []

        # Create tasks for all users
        tasks = [
            self.simulate_user_session(i, base_url, test_topic.id, metrics)
            for i in range(num_users)
        ]

        # Run all users concurrently
        start_time = time.time()
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # ── Analyze Results ───────────────────────────────────────
        print(f"\n[RESULTS] Load test completed in {total_time:.2f}s")

        # Error analysis
        total_errors = sum(m["errors"] for m in metrics)
        error_rate = (total_errors / num_users) * 100
        print(f"[RESULTS] Total errors: {total_errors} ({error_rate:.1f}%)")

        # Response time analysis
        all_response_times = []
        operation_times = {}

        for session in metrics:
            for op in session["operations"]:
                all_response_times.append(op["time"])

                op_name = op["operation"]
                if op_name not in operation_times:
                    operation_times[op_name] = []
                operation_times[op_name].append(op["time"])

        # Overall statistics
        if all_response_times:
            avg_response_time = statistics.mean(all_response_times)
            median_response_time = statistics.median(all_response_times)
            p95_response_time = statistics.quantiles(all_response_times, n=20)[18]  # 95th percentile
            max_response_time = max(all_response_times)

            print(f"\n[PERFORMANCE METRICS]")
            print(f"  Average response time: {avg_response_time*1000:.2f}ms")
            print(f"  Median response time: {median_response_time*1000:.2f}ms")
            print(f"  95th percentile: {p95_response_time*1000:.2f}ms")
            print(f"  Max response time: {max_response_time*1000:.2f}ms")

        # Per-operation statistics
        print(f"\n[PER-OPERATION METRICS]")
        for op_name, times in operation_times.items():
            avg_time = statistics.mean(times)
            max_time = max(times)
            print(f"  {op_name}: avg={avg_time*1000:.2f}ms, max={max_time*1000:.2f}ms")

        # Throughput
        throughput = num_users / total_time
        print(f"\n[THROUGHPUT] {throughput:.2f} users/second")

        # ── Assertions ────────────────────────────────────────────
        # Less than 10% error rate
        assert error_rate < 10, f"Error rate too high: {error_rate:.1f}%"

        # Average response time < 2 seconds
        if all_response_times:
            assert avg_response_time < 2.0, f"Average response time too high: {avg_response_time:.2f}s"

        # 95th percentile < 5 seconds
        if all_response_times:
            assert p95_response_time < 5.0, f"95th percentile too high: {p95_response_time:.2f}s"

        print("\n[SUCCESS] Load test passed! ✓")

    async def test_burst_traffic(self, test_client, test_topic):
        """Test handling of sudden traffic burst."""
        print("\n[LOAD TEST] Testing burst traffic...")

        base_url = "http://testserver"
        burst_size = 50
        metrics: List[Dict] = []

        # Simulate burst: all users hit at exact same time
        tasks = [
            self.simulate_user_session(i, base_url, test_topic.id, metrics)
            for i in range(burst_size)
        ]

        start_time = time.time()
        await asyncio.gather(*tasks)
        burst_time = time.time() - start_time

        print(f"[RESULTS] Burst of {burst_size} users handled in {burst_time:.2f}s")

        # Check that most requests succeeded
        total_errors = sum(m["errors"] for m in metrics)
        error_rate = (total_errors / burst_size) * 100

        print(f"[RESULTS] Burst error rate: {error_rate:.1f}%")

        # Allow higher error rate for burst (up to 20%)
        assert error_rate < 20, f"Burst error rate too high: {error_rate:.1f}%"

        print("[SUCCESS] Burst test passed! ✓")

    async def test_sustained_load(self, test_client, test_topic):
        """Test sustained load over time."""
        print("\n[LOAD TEST] Testing sustained load...")

        base_url = "http://testserver"
        users_per_wave = 10
        num_waves = 5
        wave_delay = 1.0  # seconds between waves

        all_metrics: List[Dict] = []

        for wave in range(num_waves):
            print(f"[WAVE {wave+1}/{num_waves}] Launching {users_per_wave} users...")

            wave_metrics: List[Dict] = []
            tasks = [
                self.simulate_user_session(i, base_url, test_topic.id, wave_metrics)
                for i in range(users_per_wave)
            ]

            await asyncio.gather(*tasks)
            all_metrics.extend(wave_metrics)

            # Delay before next wave
            if wave < num_waves - 1:
                await asyncio.sleep(wave_delay)

        # Analyze sustained load
        total_users = users_per_wave * num_waves
        total_errors = sum(m["errors"] for m in all_metrics)
        error_rate = (total_errors / total_users) * 100

        print(f"\n[RESULTS] Sustained load: {total_users} users")
        print(f"[RESULTS] Error rate: {error_rate:.1f}%")

        assert error_rate < 10, f"Sustained load error rate too high: {error_rate:.1f}%"

        print("[SUCCESS] Sustained load test passed! ✓")


@pytest.mark.load
@pytest.mark.asyncio
class TestDatabasePerformance:
    """Test database performance under load."""

    async def test_concurrent_database_writes(self, test_client, test_topic):
        """Test concurrent database writes."""
        print("\n[LOAD TEST] Testing concurrent database writes...")

        base_url = "http://testserver"
        num_concurrent_writes = 50

        async def create_and_submit_test(user_id: int):
            """Create and submit a mock test."""
            async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
                # Guest login
                response = await client.post("/api/v1/auth/guest")
                if response.status_code != 200:
                    return False

                token = response.json()["access_token"]
                headers = {"Authorization": f"Bearer {token}"}

                # Create mock test (writes to DB)
                response = await client.post(
                    "/api/v1/mock-tests",
                    headers=headers,
                    json={
                        "topic_id": test_topic.id,
                        "num_questions": 3,
                        "time_limit_minutes": 30
                    }
                )

                return response.status_code in [200, 201]

        # Execute concurrent writes
        start_time = time.time()
        results = await asyncio.gather(*[
            create_and_submit_test(i) for i in range(num_concurrent_writes)
        ])
        write_time = time.time() - start_time

        success_count = sum(1 for r in results if r)
        success_rate = (success_count / num_concurrent_writes) * 100

        print(f"[RESULTS] {success_count}/{num_concurrent_writes} writes succeeded ({success_rate:.1f}%)")
        print(f"[RESULTS] Completed in {write_time:.2f}s")
        print(f"[RESULTS] Write throughput: {success_count/write_time:.2f} writes/s")

        # At least 80% should succeed
        assert success_rate >= 80, f"Write success rate too low: {success_rate:.1f}%"

        print("[SUCCESS] Database write test passed! ✓")

    async def test_concurrent_database_reads(self, test_client, test_exam):
        """Test concurrent database reads."""
        print("\n[LOAD TEST] Testing concurrent database reads...")

        base_url = "http://testserver"
        num_concurrent_reads = 100

        async def read_exams():
            """Read exams from database."""
            async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
                response = await client.get("/api/v1/exams")
                return response.status_code == 200

        # Execute concurrent reads
        start_time = time.time()
        results = await asyncio.gather(*[read_exams() for _ in range(num_concurrent_reads)])
        read_time = time.time() - start_time

        success_count = sum(1 for r in results if r)
        success_rate = (success_count / num_concurrent_reads) * 100

        print(f"[RESULTS] {success_count}/{num_concurrent_reads} reads succeeded ({success_rate:.1f}%)")
        print(f"[RESULTS] Completed in {read_time:.2f}s")
        print(f"[RESULTS] Read throughput: {success_count/read_time:.2f} reads/s")

        # Should have very high success rate for reads
        assert success_rate >= 95, f"Read success rate too low: {success_rate:.1f}%"

        print("[SUCCESS] Database read test passed! ✓")


@pytest.mark.load
class TestLoadTestUtilities:
    """Utilities for generating load test reports."""

    def test_generate_load_test_report(self, tmp_path):
        """Test generating a load test report."""
        # Sample metrics
        metrics = {
            "total_users": 100,
            "total_errors": 5,
            "error_rate": 5.0,
            "avg_response_time": 0.45,
            "p95_response_time": 1.2,
            "throughput": 50.0,
        }

        # Generate report
        report_path = tmp_path / "load_test_report.txt"
        with open(report_path, "w") as f:
            f.write("STUDYPULSE LOAD TEST REPORT\n")
            f.write("=" * 50 + "\n\n")
            for key, value in metrics.items():
                f.write(f"{key}: {value}\n")

        assert report_path.exists()
        content = report_path.read_text()
        assert "LOAD TEST REPORT" in content
        print(f"[OK] Load test report generated at: {report_path}")
