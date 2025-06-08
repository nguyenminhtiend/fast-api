from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.features.auth.service import AuthService
from app.features.auth.schemas import (
    UserCreate,
    UserLogin,
    UserRegistrationResponse,
    Token,
    UserResponse,
)
from app.shared.dependencies import CurrentUser

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, username, password, and full name",
)
async def register(
    user_data: UserCreate, db: AsyncSession = Depends(get_db)
) -> UserRegistrationResponse:
    """
    Register a new user account.

    - **email**: Valid email address (required)
    - **username**: Unique username, 3-50 chars, alphanumeric + underscore/hyphen (required)
    - **full_name**: User's full name, 2-255 chars (required)
    - **password**: Strong password, min 8 chars with uppercase, lowercase, and digit (required)

    Returns the created user info and access token.
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(user_data)


@router.post(
    "/login",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Login user",
    description="Authenticate user with email and password, returns JWT token",
)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)) -> dict:
    """
    Login with email and password.

    - **email**: Registered email address
    - **password**: User's password

    Returns access token and user information.
    """
    auth_service = AuthService(db)
    return await auth_service.login_user(login_data)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout user",
    description="Logout user (client should discard token)",
)
async def logout() -> dict:
    """
    Logout user.

    Note: Since JWT tokens are stateless, logout is handled client-side
    by discarding the token. This endpoint exists for consistency.
    """
    return {"message": "Successfully logged out"}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Get the current authenticated user's profile information",
)
async def get_current_user_profile(current_user: CurrentUser) -> UserResponse:
    """
    Get current user profile.

    Requires valid JWT token in Authorization header.
    Example: Authorization: Bearer <your_jwt_token>
    """
    return UserResponse.model_validate(current_user)


# Health check for auth service
@router.get(
    "/health", status_code=status.HTTP_200_OK, summary="Auth service health check"
)
async def auth_health() -> dict:
    """Auth service health check"""
    return {"status": "healthy", "service": "auth"}
