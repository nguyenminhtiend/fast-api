import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.models import User
from app.features.auth.schemas import UserCreate, UserLogin, UserResponse
from app.features.auth.repository import UserRepository
from app.features.auth.service import AuthService
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
)


class TestSecurity:
    """Test authentication security functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPassword123"
        hashed = get_password_hash(password)

        # Password should be hashed
        assert hashed != password
        assert len(hashed) > 50  # bcrypt hashes are long

        # Verification should work
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        username = "testuser"
        token = create_access_token(data={"sub": username})

        # Token should be created
        assert token is not None
        assert len(token) > 50  # JWT tokens are long

        # Token should be verifiable
        verified_username = verify_token(token)
        assert verified_username == username

    def test_invalid_jwt_token_verification(self):
        """Test verification of invalid JWT tokens."""
        # Invalid token
        invalid_token = "invalid.jwt.token"
        result = verify_token(invalid_token)
        assert result is None

        # Empty token
        result = verify_token("")
        assert result is None


class TestUserSchemas:
    """Test Pydantic schemas for user validation."""

    def test_user_create_valid_data(self):
        """Test UserCreate schema with valid data."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "TestPassword123",
        }
        user = UserCreate(**data)

        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.password == "TestPassword123"

    def test_user_create_invalid_email(self):
        """Test UserCreate schema with invalid email."""
        data = {
            "email": "invalid-email",
            "username": "testuser",
            "full_name": "Test User",
            "password": "TestPassword123",
        }
        with pytest.raises(ValueError):
            UserCreate(**data)

    def test_user_create_invalid_username(self):
        """Test UserCreate schema with invalid username."""
        # Username too short
        data = {
            "email": "test@example.com",
            "username": "ab",
            "full_name": "Test User",
            "password": "TestPassword123",
        }
        with pytest.raises(ValueError):
            UserCreate(**data)

        # Username with invalid characters
        data["username"] = "test user!"
        with pytest.raises(ValueError):
            UserCreate(**data)

    def test_user_create_invalid_password(self):
        """Test UserCreate schema with invalid password."""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "weak",  # Too short, no uppercase, no digit
        }
        with pytest.raises(ValueError):
            UserCreate(**data)

    def test_user_login_schema(self):
        """Test UserLogin schema."""
        data = {"email": "test@example.com", "password": "TestPassword123"}
        login = UserLogin(**data)

        assert login.email == "test@example.com"
        assert login.password == "TestPassword123"


@pytest_asyncio.fixture
async def mock_db_session():
    """Mock database session."""
    return Mock(spec=AsyncSession)


@pytest_asyncio.fixture
async def user_repository(mock_db_session):
    """Create UserRepository with mocked database."""
    return UserRepository(mock_db_session)


class TestUserRepository:
    """Test UserRepository data access layer."""

    @pytest_asyncio.fixture
    async def sample_user(self):
        """Sample user for testing."""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            hashed_password=get_password_hash("TestPassword123"),
            is_active=True,
            is_verified=False,
        )

    async def test_get_by_email(self, user_repository, mock_db_session, sample_user):
        """Test getting user by email."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_email("test@example.com")

        assert result == sample_user
        mock_db_session.execute.assert_called_once()

    async def test_get_by_username(self, user_repository, mock_db_session, sample_user):
        """Test getting user by username."""
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.get_by_username("testuser")

        assert result == sample_user
        mock_db_session.execute.assert_called_once()

    async def test_email_exists(self, user_repository, mock_db_session):
        """Test checking if email exists."""
        # Mock email exists
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = 1  # User ID exists
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.email_exists("test@example.com")

        assert result is True
        mock_db_session.execute.assert_called_once()

    async def test_email_not_exists(self, user_repository, mock_db_session):
        """Test checking if email doesn't exist."""
        # Mock email doesn't exist
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = await user_repository.email_exists("nonexistent@example.com")

        assert result is False
        mock_db_session.execute.assert_called_once()


class TestAuthService:
    """Test AuthService business logic layer."""

    @pytest_asyncio.fixture
    async def auth_service(self, mock_db_session):
        """Create AuthService with mocked database."""
        return AuthService(mock_db_session)

    @pytest_asyncio.fixture
    async def user_create_data(self):
        """Sample user creation data."""
        return UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="TestPassword123",
        )

    async def test_register_user_success(self, auth_service, user_create_data):
        """Test successful user registration."""
        # Mock repository methods
        with (
            patch.object(
                auth_service.user_repo,
                "email_exists",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                auth_service.user_repo,
                "username_exists",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                auth_service.user_repo, "create_user", new_callable=AsyncMock
            ) as mock_create,
        ):

            # Mock created user
            mock_user = Mock()
            mock_user.id = 1
            mock_user.email = user_create_data.email
            mock_user.username = user_create_data.username
            mock_user.full_name = user_create_data.full_name
            mock_user.is_active = True
            mock_user.is_verified = False
            mock_user.created_at = datetime.now()
            mock_user.updated_at = datetime.now()
            mock_create.return_value = mock_user

            result = await auth_service.register_user(user_create_data)

            assert result.message == "User registered successfully"
            assert result.user.email == user_create_data.email
            assert result.access_token is not None
            assert result.token_type == "bearer"

    async def test_register_user_email_exists(self, auth_service, user_create_data):
        """Test registration with existing email."""
        # Mock email exists
        with patch.object(
            auth_service.user_repo,
            "email_exists",
            new_callable=AsyncMock,
            return_value=True,
        ):

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(user_create_data)

            assert exc_info.value.status_code == 400
            assert "Email already registered" in str(exc_info.value.detail)

    async def test_register_user_username_exists(self, auth_service, user_create_data):
        """Test registration with existing username."""
        # Mock email doesn't exist but username does
        with (
            patch.object(
                auth_service.user_repo,
                "email_exists",
                new_callable=AsyncMock,
                return_value=False,
            ),
            patch.object(
                auth_service.user_repo,
                "username_exists",
                new_callable=AsyncMock,
                return_value=True,
            ),
        ):

            with pytest.raises(HTTPException) as exc_info:
                await auth_service.register_user(user_create_data)

            assert exc_info.value.status_code == 400
            assert "Username already taken" in str(exc_info.value.detail)

    async def test_authenticate_user_success(self, auth_service):
        """Test successful user authentication."""
        login_data = UserLogin(email="test@example.com", password="TestPassword123")

        # Mock user with correct password hash
        mock_user = Mock()
        mock_user.email = login_data.email
        mock_user.hashed_password = get_password_hash(login_data.password)
        mock_user.is_active = True

        with patch.object(
            auth_service.user_repo,
            "get_by_email",
            new_callable=AsyncMock,
            return_value=mock_user,
        ):
            result = await auth_service.authenticate_user(login_data)

            assert result == mock_user

    async def test_authenticate_user_wrong_password(self, auth_service):
        """Test authentication with wrong password."""
        login_data = UserLogin(email="test@example.com", password="WrongPassword")

        # Mock user with different password hash
        mock_user = Mock()
        mock_user.email = login_data.email
        mock_user.hashed_password = get_password_hash("DifferentPassword123")
        mock_user.is_active = True

        with patch.object(
            auth_service.user_repo,
            "get_by_email",
            new_callable=AsyncMock,
            return_value=mock_user,
        ):
            result = await auth_service.authenticate_user(login_data)

            assert result is None

    async def test_authenticate_user_not_found(self, auth_service):
        """Test authentication with non-existent user."""
        login_data = UserLogin(
            email="nonexistent@example.com", password="TestPassword123"
        )

        with patch.object(
            auth_service.user_repo,
            "get_by_email",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await auth_service.authenticate_user(login_data)

            assert result is None

    async def test_authenticate_inactive_user(self, auth_service):
        """Test authentication with inactive user."""
        login_data = UserLogin(email="test@example.com", password="TestPassword123")

        # Mock inactive user
        mock_user = Mock()
        mock_user.email = login_data.email
        mock_user.hashed_password = get_password_hash(login_data.password)
        mock_user.is_active = False

        with patch.object(
            auth_service.user_repo,
            "get_by_email",
            new_callable=AsyncMock,
            return_value=mock_user,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.authenticate_user(login_data)

            assert exc_info.value.status_code == 400
            assert "Inactive user account" in str(exc_info.value.detail)
