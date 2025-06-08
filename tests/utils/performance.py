import time
import asyncio
import statistics
from typing import List, Dict, Any, Callable
from httpx import AsyncClient
from fastapi.testclient import TestClient


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.elapsed = self.end_time - self.start_time


class PerformanceBenchmark:
    """Performance benchmarking utilities for API endpoints."""

    @staticmethod
    def measure_endpoint_performance(
        client: TestClient, method: str, url: str, iterations: int = 100, **kwargs
    ) -> Dict[str, Any]:
        """Measure performance of an API endpoint."""
        times = []
        status_codes = []

        for _ in range(iterations):
            with PerformanceTimer() as timer:
                if method.upper() == "GET":
                    response = client.get(url, **kwargs)
                elif method.upper() == "POST":
                    response = client.post(url, **kwargs)
                elif method.upper() == "PUT":
                    response = client.put(url, **kwargs)
                elif method.upper() == "DELETE":
                    response = client.delete(url, **kwargs)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

            times.append(timer.elapsed)
            status_codes.append(response.status_code)

        return {
            "iterations": iterations,
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "median_time": statistics.median(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "percentile_95": sorted(times)[int(0.95 * len(times))],
            "percentile_99": sorted(times)[int(0.99 * len(times))],
            "status_codes": set(status_codes),
            "success_rate": sum(1 for code in status_codes if 200 <= code < 300)
            / len(status_codes),
            "raw_times": times,
        }

    @staticmethod
    async def measure_async_endpoint_performance(
        client: AsyncClient, method: str, url: str, iterations: int = 100, **kwargs
    ) -> Dict[str, Any]:
        """Measure performance of an async API endpoint."""
        times = []
        status_codes = []

        for _ in range(iterations):
            start_time = time.perf_counter()

            if method.upper() == "GET":
                response = await client.get(url, **kwargs)
            elif method.upper() == "POST":
                response = await client.post(url, **kwargs)
            elif method.upper() == "PUT":
                response = await client.put(url, **kwargs)
            elif method.upper() == "DELETE":
                response = await client.delete(url, **kwargs)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            end_time = time.perf_counter()
            times.append(end_time - start_time)
            status_codes.append(response.status_code)

        return {
            "iterations": iterations,
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "median_time": statistics.median(times),
            "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
            "percentile_95": sorted(times)[int(0.95 * len(times))],
            "percentile_99": sorted(times)[int(0.99 * len(times))],
            "status_codes": set(status_codes),
            "success_rate": sum(1 for code in status_codes if 200 <= code < 300)
            / len(status_codes),
            "raw_times": times,
        }

    @staticmethod
    async def measure_concurrent_requests(
        client: AsyncClient,
        method: str,
        url: str,
        concurrent_users: int = 10,
        requests_per_user: int = 10,
        **kwargs,
    ) -> Dict[str, Any]:
        """Measure performance under concurrent load."""

        async def user_requests(user_id: int) -> List[float]:
            times = []
            for _ in range(requests_per_user):
                start_time = time.perf_counter()

                if method.upper() == "GET":
                    response = await client.get(url, **kwargs)
                elif method.upper() == "POST":
                    # Add user_id to make each request unique if needed
                    request_kwargs = kwargs.copy()
                    if "json" in request_kwargs:
                        request_kwargs["json"] = request_kwargs["json"].copy()
                        if "username" in request_kwargs["json"]:
                            request_kwargs["json"]["username"] += f"_{user_id}"
                        if "email" in request_kwargs["json"]:
                            email_parts = request_kwargs["json"]["email"].split("@")
                            request_kwargs["json"][
                                "email"
                            ] = f"{email_parts[0]}_{user_id}@{email_parts[1]}"
                    response = await client.post(url, **request_kwargs)
                else:
                    response = await client.request(method, url, **kwargs)

                end_time = time.perf_counter()
                times.append(end_time - start_time)

            return times

        # Execute concurrent requests
        start_time = time.perf_counter()
        tasks = [user_requests(i) for i in range(concurrent_users)]
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        # Flatten results
        all_times = [time for user_times in results for time in user_times]

        return {
            "concurrent_users": concurrent_users,
            "requests_per_user": requests_per_user,
            "total_requests": len(all_times),
            "total_time": total_time,
            "requests_per_second": len(all_times) / total_time,
            "avg_response_time": statistics.mean(all_times),
            "min_response_time": min(all_times),
            "max_response_time": max(all_times),
            "median_response_time": statistics.median(all_times),
            "percentile_95": sorted(all_times)[int(0.95 * len(all_times))],
            "percentile_99": sorted(all_times)[int(0.99 * len(all_times))],
        }


class LoadTestScenarios:
    """Common load test scenarios for authentication APIs."""

    @staticmethod
    def generate_user_data(user_id: int) -> Dict[str, str]:
        """Generate unique user data for load testing."""
        return {
            "email": f"loadtest{user_id}@example.com",
            "username": f"loadtest{user_id}",
            "full_name": f"Load Test User {user_id}",
            "password": "LoadTestPassword123",
        }

    @staticmethod
    async def registration_load_test(
        client: AsyncClient, concurrent_users: int = 50, registrations_per_user: int = 5
    ) -> Dict[str, Any]:
        """Load test user registration endpoint."""

        async def register_users(user_base_id: int) -> List[Dict[str, Any]]:
            results = []
            for i in range(registrations_per_user):
                user_id = user_base_id * registrations_per_user + i
                user_data = LoadTestScenarios.generate_user_data(user_id)

                start_time = time.perf_counter()
                response = await client.post("/api/v1/auth/register", json=user_data)
                end_time = time.perf_counter()

                results.append(
                    {
                        "user_id": user_id,
                        "response_time": end_time - start_time,
                        "status_code": response.status_code,
                        "success": 200 <= response.status_code < 300,
                    }
                )

            return results

        # Execute concurrent registrations
        start_time = time.perf_counter()
        tasks = [register_users(i) for i in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        # Flatten and analyze results
        flat_results = [
            result for user_results in all_results for result in user_results
        ]
        response_times = [r["response_time"] for r in flat_results]
        success_count = sum(1 for r in flat_results if r["success"])

        return {
            "scenario": "registration_load_test",
            "concurrent_users": concurrent_users,
            "registrations_per_user": registrations_per_user,
            "total_registrations": len(flat_results),
            "total_time": total_time,
            "registrations_per_second": len(flat_results) / total_time,
            "success_rate": success_count / len(flat_results),
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "median_response_time": statistics.median(response_times),
            "percentile_95": sorted(response_times)[int(0.95 * len(response_times))],
            "percentile_99": sorted(response_times)[int(0.99 * len(response_times))],
        }

    @staticmethod
    async def login_load_test(
        client: AsyncClient, concurrent_users: int = 100, logins_per_user: int = 10
    ) -> Dict[str, Any]:
        """Load test user login endpoint."""

        # First, register a test user for login
        test_user = LoadTestScenarios.generate_user_data(999999)
        await client.post("/api/v1/auth/register", json=test_user)

        async def login_attempts(user_id: int) -> List[Dict[str, Any]]:
            results = []
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"],
            }

            for _ in range(logins_per_user):
                start_time = time.perf_counter()
                response = await client.post("/api/v1/auth/login", json=login_data)
                end_time = time.perf_counter()

                results.append(
                    {
                        "user_id": user_id,
                        "response_time": end_time - start_time,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                    }
                )

            return results

        # Execute concurrent logins
        start_time = time.perf_counter()
        tasks = [login_attempts(i) for i in range(concurrent_users)]
        all_results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time

        # Analyze results
        flat_results = [
            result for user_results in all_results for result in user_results
        ]
        response_times = [r["response_time"] for r in flat_results]
        success_count = sum(1 for r in flat_results if r["success"])

        return {
            "scenario": "login_load_test",
            "concurrent_users": concurrent_users,
            "logins_per_user": logins_per_user,
            "total_logins": len(flat_results),
            "total_time": total_time,
            "logins_per_second": len(flat_results) / total_time,
            "success_rate": success_count / len(flat_results),
            "avg_response_time": statistics.mean(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "median_response_time": statistics.median(response_times),
            "percentile_95": sorted(response_times)[int(0.95 * len(response_times))],
            "percentile_99": sorted(response_times)[int(0.99 * len(response_times))],
        }
