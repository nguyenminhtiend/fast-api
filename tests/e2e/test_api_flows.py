import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient


class TestAuthenticationE2E:
    """End-to-end tests for authentication API workflows."""

    def test_user_registration_success(self, test_client: TestClient):
        """Test successful user registration via API."""
        user_data = {
            "email": "e2e@example.com",
            "username": "e2euser",
            "full_name": "E2E Test User",
            "password": "E2EPassword123",
        }

        response = test_client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()

        assert data["message"] == "User registered successfully"
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["username"] == user_data["username"]
        assert data["user"]["full_name"] == user_data["full_name"]
        assert data["user"]["is_active"] is True
        assert data["user"]["is_verified"] is False
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_user_registration_validation_errors(self, test_client: TestClient):
        """Test user registration with validation errors."""
        # Test invalid email
        invalid_data = {
            "email": "invalid-email",
            "username": "testuser",
            "full_name": "Test User",
            "password": "TestPassword123",
        }

        response = test_client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

        # Test weak password
        invalid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "weak",
        }

        response = test_client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_user_registration_duplicate_email(self, test_client: TestClient):
        """Test registration with duplicate email."""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "full_name": "User One",
            "password": "Password123",
        }

        # Register first user
        response = test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register second user with same email
        user_data["username"] = "user2"  # Different username
        response = test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_user_registration_duplicate_username(self, test_client: TestClient):
        """Test registration with duplicate username."""
        user_data = {
            "email": "user1@example.com",
            "username": "duplicateuser",
            "full_name": "User One",
            "password": "Password123",
        }

        # Register first user
        response = test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        # Try to register second user with same username
        user_data["email"] = "user2@example.com"  # Different email
        response = test_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]

    def test_user_login_success(self, test_client: TestClient):
        """Test successful user login."""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "username": "loginuser",
            "full_name": "Login User",
            "password": "LoginPassword123",
        }

        register_response = test_client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201

        # Now test login
        login_data = {"email": "login@example.com", "password": "LoginPassword123"}

        response = test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == login_data["email"]
        assert data["user"]["username"] == user_data["username"]

    def test_user_login_invalid_credentials(self, test_client: TestClient):
        """Test login with invalid credentials."""
        # First register a user
        user_data = {
            "email": "invalid@example.com",
            "username": "invaliduser",
            "full_name": "Invalid User",
            "password": "ValidPassword123",
        }

        test_client.post("/api/v1/auth/register", json=user_data)

        # Test wrong password
        login_data = {"email": "invalid@example.com", "password": "WrongPassword123"}

        response = test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

        # Test non-existent user
        login_data = {
            "email": "nonexistent@example.com",
            "password": "ValidPassword123",
        }

        response = test_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401

    def test_protected_route_with_valid_token(self, test_client: TestClient):
        """Test accessing protected route with valid token."""
        # Register and get token
        user_data = {
            "email": "protected@example.com",
            "username": "protecteduser",
            "full_name": "Protected User",
            "password": "ProtectedPassword123",
        }

        register_response = test_client.post("/api/v1/auth/register", json=user_data)
        token = register_response.json()["access_token"]

        # Access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = test_client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]

    def test_protected_route_without_token(self, test_client: TestClient):
        """Test accessing protected route without token."""
        response = test_client.get("/api/v1/auth/me")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]

    def test_protected_route_with_invalid_token(self, test_client: TestClient):
        """Test accessing protected route with invalid token."""
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = test_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_logout_endpoint(self, test_client: TestClient):
        """Test logout endpoint."""
        response = test_client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_complete_user_flow(self, test_client: TestClient):
        """Test complete user flow: register -> login -> access protected route."""
        # Step 1: Register
        user_data = {
            "email": "complete@example.com",
            "username": "completeuser",
            "full_name": "Complete User",
            "password": "CompletePassword123",
        }

        register_response = test_client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 201
        register_token = register_response.json()["access_token"]

        # Step 2: Login (get new token)
        login_data = {
            "email": "complete@example.com",
            "password": "CompletePassword123",
        }

        login_response = test_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        login_token = login_response.json()["access_token"]

        # Step 3: Access protected route with register token
        headers = {"Authorization": f"Bearer {register_token}"}
        me_response = test_client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == user_data["email"]

        # Step 4: Access protected route with login token
        headers = {"Authorization": f"Bearer {login_token}"}
        me_response = test_client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == user_data["email"]

        # Step 5: Logout
        logout_response = test_client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200


class TestAPIHealthChecks:
    """Test API health check endpoints."""

    def test_root_endpoint(self, test_client: TestClient):
        """Test root API endpoint."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data

    def test_health_endpoint(self, test_client: TestClient):
        """Test main health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "task-management"

    def test_auth_health_endpoint(self, test_client: TestClient):
        """Test auth service health check."""
        response = test_client.get("/api/v1/auth/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth"


class TestAsyncClientFlows:
    """Test flows using async client for more realistic scenarios."""

    async def test_concurrent_registrations(self, async_client: AsyncClient):
        """Test concurrent user registrations."""
        import asyncio

        async def register_user(client: AsyncClient, user_num: int):
            user_data = {
                "email": f"concurrent{user_num}@example.com",
                "username": f"concurrent{user_num}",
                "full_name": f"Concurrent User {user_num}",
                "password": "ConcurrentPassword123",
            }
            return await client.post("/api/v1/auth/register", json=user_data)

        # Register multiple users concurrently
        tasks = [register_user(async_client, i) for i in range(1, 6)]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 201
            data = response.json()
            assert "access_token" in data
            assert data["message"] == "User registered successfully"

    async def test_token_authentication_flow(self, async_client: AsyncClient):
        """Test token-based authentication flow."""
        # Register user
        user_data = {
            "email": "async@example.com",
            "username": "asyncuser",
            "full_name": "Async User",
            "password": "AsyncPassword123",
        }

        register_response = await async_client.post(
            "/api/v1/auth/register", json=user_data
        )
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]

        # Use token to access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        me_response = await async_client.get("/api/v1/auth/me", headers=headers)

        assert me_response.status_code == 200
        user_info = me_response.json()
        assert user_info["email"] == user_data["email"]
        assert user_info["username"] == user_data["username"]
