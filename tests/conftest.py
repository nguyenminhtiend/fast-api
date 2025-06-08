import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.features.auth.models import User
from app.features.auth.schemas import UserCreate
from app.features.auth.service import AuthService
from app.core.security import get_password_hash

# Test Database URL (SQLite for faster tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
TEST_SYNC_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with test_session_maker() as session:
        yield session

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the get_db dependency for testing."""

    async def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture
def test_client(override_get_db) -> TestClient:
    """Create a test client with database dependency override."""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        password="TestPassword123",
    )

    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict:
    """Create authorization headers with JWT token for test user."""
    from app.core.security import create_access_token

    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "full_name": "New User",
        "password": "NewPassword123",
    }


@pytest.fixture
def invalid_user_data() -> dict:
    """Invalid user data for testing validation."""
    return {
        "email": "invalid-email",
        "username": "ab",  # Too short
        "full_name": "",  # Empty
        "password": "weak",  # Too weak
    }


# Test utilities
class TestUtils:
    """Utility functions for testing."""

    @staticmethod
    def extract_token_from_response(response_data: dict) -> str:
        """Extract access token from API response."""
        return response_data.get("access_token")

    @staticmethod
    def create_auth_header(token: str) -> dict:
        """Create authorization header from token."""
        return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_utils() -> TestUtils:
    """Test utilities fixture."""
    return TestUtils()
