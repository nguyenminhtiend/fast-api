import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User
from app.features.auth.schemas import UserCreate, UserLogin
from app.features.auth.repository import UserRepository
from app.features.auth.service import AuthService
from app.core.security import verify_password, get_password_hash


class TestAuthIntegration:
    """Integration tests for authentication with real database operations."""

    async def test_user_repository_crud_operations(self, db_session: AsyncSession):
        """Test complete CRUD operations on User repository."""
        repo = UserRepository(db_session)

        # Test user creation
        user_data = UserCreate(
            email="integration@example.com",
            username="integrationuser",
            full_name="Integration Test User",
            password="IntegrationPass123",
        )

        # Create user
        created_user = await repo.create_user(user_data)
        assert created_user.id is not None
        assert created_user.email == user_data.email
        assert created_user.username == user_data.username
        assert created_user.full_name == user_data.full_name
        assert verify_password(user_data.password, created_user.hashed_password)
        assert created_user.is_active is True
        assert created_user.is_verified is False

        # Test get by email
        found_user = await repo.get_by_email(user_data.email)
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.email == created_user.email

        # Test get by username
        found_user = await repo.get_by_username(user_data.username)
        assert found_user is not None
        assert found_user.id == created_user.id
        assert found_user.username == created_user.username

        # Test get by ID
        found_user = await repo.get_by_id(created_user.id)
        assert found_user is not None
        assert found_user.id == created_user.id

        # Test email exists
        assert await repo.email_exists(user_data.email) is True
        assert await repo.email_exists("nonexistent@example.com") is False

        # Test username exists
        assert await repo.username_exists(user_data.username) is True
        assert await repo.username_exists("nonexistentuser") is False

    async def test_duplicate_email_constraint(self, db_session: AsyncSession):
        """Test that duplicate emails are prevented."""
        repo = UserRepository(db_session)

        # Create first user
        user_data1 = UserCreate(
            email="duplicate@example.com",
            username="user1",
            full_name="User One",
            password="Password123",
        )
        await repo.create_user(user_data1)

        # Try to create second user with same email
        user_data2 = UserCreate(
            email="duplicate@example.com",  # Same email
            username="user2",
            full_name="User Two",
            password="Password123",
        )

        with pytest.raises(ValueError, match="Email already registered"):
            await repo.create_user(user_data2)

    async def test_duplicate_username_constraint(self, db_session: AsyncSession):
        """Test that duplicate usernames are prevented."""
        repo = UserRepository(db_session)

        # Create first user
        user_data1 = UserCreate(
            email="user1@example.com",
            username="duplicateuser",
            full_name="User One",
            password="Password123",
        )
        await repo.create_user(user_data1)

        # Try to create second user with same username
        user_data2 = UserCreate(
            email="user2@example.com",
            username="duplicateuser",  # Same username
            full_name="User Two",
            password="Password123",
        )

        with pytest.raises(ValueError, match="Username already taken"):
            await repo.create_user(user_data2)

    async def test_auth_service_registration_flow(self, db_session: AsyncSession):
        """Test complete user registration flow."""
        service = AuthService(db_session)

        user_data = UserCreate(
            email="service@example.com",
            username="serviceuser",
            full_name="Service Test User",
            password="ServicePass123",
        )

        # Register user
        result = await service.register_user(user_data)

        assert result.message == "User registered successfully"
        assert result.user.email == user_data.email
        assert result.user.username == user_data.username
        assert result.user.full_name == user_data.full_name
        assert result.user.is_active is True
        assert result.user.is_verified is False
        assert result.access_token is not None
        assert result.token_type == "bearer"

        # Verify user was actually created in database
        repo = UserRepository(db_session)
        db_user = await repo.get_by_email(user_data.email)
        assert db_user is not None
        assert db_user.email == user_data.email

    async def test_auth_service_login_flow(self, db_session: AsyncSession):
        """Test complete user login flow."""
        service = AuthService(db_session)

        # First register a user
        user_data = UserCreate(
            email="login@example.com",
            username="loginuser",
            full_name="Login Test User",
            password="LoginPass123",
        )
        await service.register_user(user_data)

        # Now test login
        login_data = UserLogin(email="login@example.com", password="LoginPass123")

        result = await service.login_user(login_data)

        assert result["access_token"] is not None
        assert result["token_type"] == "bearer"
        assert result["user"].email == login_data.email
        assert result["user"].username == user_data.username

    async def test_auth_service_authentication_methods(self, db_session: AsyncSession):
        """Test user authentication methods."""
        service = AuthService(db_session)

        # Register user
        user_data = UserCreate(
            email="auth@example.com",
            username="authuser",
            full_name="Auth Test User",
            password="AuthPass123",
        )
        await service.register_user(user_data)

        # Test successful authentication
        login_data = UserLogin(email="auth@example.com", password="AuthPass123")
        user = await service.authenticate_user(login_data)
        assert user is not None
        assert user.email == "auth@example.com"

        # Test wrong password
        wrong_login = UserLogin(email="auth@example.com", password="WrongPassword")
        user = await service.authenticate_user(wrong_login)
        assert user is None

        # Test non-existent user
        fake_login = UserLogin(email="fake@example.com", password="AuthPass123")
        user = await service.authenticate_user(fake_login)
        assert user is None

    async def test_password_hashing_integration(self, db_session: AsyncSession):
        """Test that passwords are properly hashed and verified."""
        repo = UserRepository(db_session)

        user_data = UserCreate(
            email="hash@example.com",
            username="hashuser",
            full_name="Hash Test User",
            password="PlainTextPassword123",
        )

        # Create user
        created_user = await repo.create_user(user_data)

        # Verify password is hashed
        assert created_user.hashed_password != user_data.password
        assert len(created_user.hashed_password) > 50  # bcrypt hashes are long

        # Verify password can be verified
        assert verify_password(user_data.password, created_user.hashed_password) is True
        assert verify_password("wrong_password", created_user.hashed_password) is False

    async def test_user_update_operations(self, db_session: AsyncSession):
        """Test user update operations."""
        repo = UserRepository(db_session)

        # Create user
        user_data = UserCreate(
            email="update@example.com",
            username="updateuser",
            full_name="Update Test User",
            password="UpdatePass123",
        )
        created_user = await repo.create_user(user_data)

        # Update user
        created_user.full_name = "Updated Full Name"
        created_user.is_verified = True

        updated_user = await repo.update_user(created_user)

        assert updated_user.full_name == "Updated Full Name"
        assert updated_user.is_verified is True

        # Verify in database
        db_user = await repo.get_by_id(created_user.id)
        assert db_user.full_name == "Updated Full Name"
        assert db_user.is_verified is True
