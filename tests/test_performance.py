import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from tests.utils.performance import PerformanceBenchmark, LoadTestScenarios


class TestAuthenticationPerformance:
    """Performance tests for authentication endpoints."""

    def test_health_endpoint_performance(self, test_client: TestClient):
        """Test health endpoint performance."""
        stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client, method="GET", url="/health", iterations=100
        )

        # Health endpoint should be very fast
        assert stats["avg_time"] < 0.01  # Less than 10ms average
        assert stats["percentile_95"] < 0.02  # 95% under 20ms
        assert stats["success_rate"] == 1.0  # 100% success

        print(
            f"Health endpoint performance: {stats['avg_time']:.4f}s avg, "
            f"{stats['percentile_95']:.4f}s 95th percentile"
        )

    def test_registration_endpoint_performance(self, test_client: TestClient):
        """Test user registration endpoint performance."""
        user_data = {
            "email": "perf@example.com",
            "username": "perfuser",
            "full_name": "Performance User",
            "password": "PerfPassword123",
        }

        # Test single registration performance
        stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client,
            method="POST",
            url="/api/v1/auth/register",
            iterations=1,  # Only test once due to unique constraints
            json=user_data,
        )

        # Registration should complete reasonably fast
        assert stats["avg_time"] < 1.0  # Less than 1 second
        assert stats["success_rate"] == 1.0  # 100% success

        print(f"Registration performance: {stats['avg_time']:.4f}s")

    def test_login_endpoint_performance(self, test_client: TestClient):
        """Test user login endpoint performance."""
        # First register a user
        user_data = {
            "email": "loginperf@example.com",
            "username": "loginperfuser",
            "full_name": "Login Perf User",
            "password": "LoginPerfPassword123",
        }
        test_client.post("/api/v1/auth/register", json=user_data)

        # Test login performance
        login_data = {
            "email": "loginperf@example.com",
            "password": "LoginPerfPassword123",
        }

        stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client,
            method="POST",
            url="/api/v1/auth/login",
            iterations=50,
            json=login_data,
        )

        # Login should be fast
        assert stats["avg_time"] < 0.5  # Less than 500ms average
        assert stats["percentile_95"] < 1.0  # 95% under 1 second
        assert stats["success_rate"] == 1.0  # 100% success

        print(
            f"Login performance: {stats['avg_time']:.4f}s avg, "
            f"{stats['percentile_95']:.4f}s 95th percentile"
        )

    def test_protected_endpoint_performance(self, test_client: TestClient):
        """Test protected endpoint performance."""
        # Register user and get token
        user_data = {
            "email": "protectedperf@example.com",
            "username": "protectedperfuser",
            "full_name": "Protected Perf User",
            "password": "ProtectedPerfPassword123",
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test protected endpoint performance
        stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client,
            method="GET",
            url="/api/v1/auth/me",
            iterations=100,
            headers=headers,
        )

        # Protected endpoint should be fast
        assert stats["avg_time"] < 0.1  # Less than 100ms average
        assert stats["percentile_95"] < 0.2  # 95% under 200ms
        assert stats["success_rate"] == 1.0  # 100% success

        print(
            f"Protected endpoint performance: {stats['avg_time']:.4f}s avg, "
            f"{stats['percentile_95']:.4f}s 95th percentile"
        )


class TestAsyncPerformance:
    """Async performance tests with concurrent load."""

    async def test_async_health_performance(self, async_client: AsyncClient):
        """Test async health endpoint performance."""
        stats = await PerformanceBenchmark.measure_async_endpoint_performance(
            client=async_client, method="GET", url="/health", iterations=200
        )

        assert stats["avg_time"] < 0.01  # Very fast
        assert stats["success_rate"] == 1.0

        print(f"Async health performance: {stats['avg_time']:.4f}s avg")

    async def test_concurrent_login_performance(self, async_client: AsyncClient):
        """Test concurrent login performance."""
        # Register a test user
        user_data = {
            "email": "concurrentlogin@example.com",
            "username": "concurrentloginuser",
            "full_name": "Concurrent Login User",
            "password": "ConcurrentLoginPassword123",
        }
        await async_client.post("/api/v1/auth/register", json=user_data)

        # Test concurrent logins
        login_data = {
            "email": "concurrentlogin@example.com",
            "password": "ConcurrentLoginPassword123",
        }

        stats = await PerformanceBenchmark.measure_concurrent_requests(
            client=async_client,
            method="POST",
            url="/api/v1/auth/login",
            concurrent_users=10,
            requests_per_user=5,
            json=login_data,
        )

        # Should handle concurrent logins well
        assert stats["requests_per_second"] > 20  # At least 20 RPS
        assert stats["avg_response_time"] < 1.0  # Average under 1 second

        print(
            f"Concurrent login performance: {stats['requests_per_second']:.1f} RPS, "
            f"{stats['avg_response_time']:.4f}s avg response time"
        )

    @pytest.mark.slow
    async def test_registration_load_test(self, async_client: AsyncClient):
        """Load test for user registration (marked as slow)."""
        stats = await LoadTestScenarios.registration_load_test(
            client=async_client, concurrent_users=20, registrations_per_user=3
        )

        # Should handle registration load
        assert stats["success_rate"] > 0.95  # At least 95% success
        assert stats["registrations_per_second"] > 10  # At least 10 RPS
        assert stats["avg_response_time"] < 2.0  # Average under 2 seconds

        print(
            f"Registration load test: {stats['registrations_per_second']:.1f} RPS, "
            f"{stats['success_rate']:.2%} success rate, "
            f"{stats['avg_response_time']:.4f}s avg response time"
        )

    @pytest.mark.slow
    async def test_login_load_test(self, async_client: AsyncClient):
        """Load test for user login (marked as slow)."""
        stats = await LoadTestScenarios.login_load_test(
            client=async_client, concurrent_users=50, logins_per_user=5
        )

        # Should handle login load well
        assert stats["success_rate"] > 0.99  # At least 99% success
        assert stats["logins_per_second"] > 50  # At least 50 RPS
        assert stats["avg_response_time"] < 1.0  # Average under 1 second

        print(
            f"Login load test: {stats['logins_per_second']:.1f} RPS, "
            f"{stats['success_rate']:.2%} success rate, "
            f"{stats['avg_response_time']:.4f}s avg response time"
        )


class TestPerformanceRegression:
    """Performance regression tests to ensure API doesn't slow down."""

    PERFORMANCE_THRESHOLDS = {
        "health_endpoint_avg": 0.01,  # 10ms
        "login_endpoint_avg": 0.5,  # 500ms
        "registration_endpoint_max": 2.0,  # 2s
        "protected_endpoint_95th": 0.2,  # 200ms
    }

    def test_performance_thresholds(self, test_client: TestClient):
        """Test that all endpoints meet performance thresholds."""
        results = {}

        # Test health endpoint
        health_stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client, method="GET", url="/health", iterations=50
        )
        results["health_endpoint_avg"] = health_stats["avg_time"]

        # Test login endpoint
        user_data = {
            "email": "thresholdtest@example.com",
            "username": "thresholdtestuser",
            "full_name": "Threshold Test User",
            "password": "ThresholdPassword123",
        }
        test_client.post("/api/v1/auth/register", json=user_data)

        login_data = {
            "email": "thresholdtest@example.com",
            "password": "ThresholdPassword123",
        }
        login_stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client,
            method="POST",
            url="/api/v1/auth/login",
            iterations=20,
            json=login_data,
        )
        results["login_endpoint_avg"] = login_stats["avg_time"]

        # Test registration endpoint (single request)
        reg_data = {
            "email": "regthreshold@example.com",
            "username": "regthresholduser",
            "full_name": "Registration Threshold User",
            "password": "RegThresholdPassword123",
        }
        reg_stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client,
            method="POST",
            url="/api/v1/auth/register",
            iterations=1,
            json=reg_data,
        )
        results["registration_endpoint_max"] = reg_stats["max_time"]

        # Test protected endpoint
        token_response = test_client.post("/api/v1/auth/login", json=login_data)
        token = token_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        protected_stats = PerformanceBenchmark.measure_endpoint_performance(
            client=test_client,
            method="GET",
            url="/api/v1/auth/me",
            iterations=50,
            headers=headers,
        )
        results["protected_endpoint_95th"] = protected_stats["percentile_95"]

        # Check all thresholds
        for metric, actual_value in results.items():
            threshold = self.PERFORMANCE_THRESHOLDS[metric]
            assert actual_value <= threshold, (
                f"Performance regression: {metric} = {actual_value:.4f}s "
                f"exceeds threshold of {threshold:.4f}s"
            )

        print("Performance thresholds check:")
        for metric, value in results.items():
            threshold = self.PERFORMANCE_THRESHOLDS[metric]
            print(f"  {metric}: {value:.4f}s (threshold: {threshold:.4f}s) ✓")


# Custom pytest markers for test categorization
pytest.mark.performance = pytest.mark.mark(
    "performance", reason="Performance tests that measure response times and throughput"
)

pytest.mark.slow = pytest.mark.mark(
    "slow", reason="Tests that take longer to run, typically load tests"
)
