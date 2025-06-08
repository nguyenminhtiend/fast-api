from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.features.auth.repository import UserRepository
from app.features.auth.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserRegistrationResponse,
)
from app.features.auth.models import User
from app.core.security import (
    verify_password,
    create_access_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)


class AuthService:
    """Authentication service for business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(self, user_data: UserCreate) -> UserRegistrationResponse:
        """Register a new user"""
        # Check if email already exists
        if await self.user_repo.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Check if username already exists
        if await self.user_repo.username_exists(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
            )

        try:
            # Create user
            user = await self.user_repo.create_user(user_data)

            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.username}, expires_delta=access_token_expires
            )

            # Convert to response model
            user_response = UserResponse.model_validate(user)

            return UserRegistrationResponse(
                message="User registered successfully",
                user=user_response,
                access_token=access_token,
                token_type="bearer",
            )

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during registration",
            )

    async def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """Authenticate user by email and password"""
        user = await self.user_repo.get_by_email(login_data.email)

        if not user:
            return None

        if not verify_password(login_data.password, user.hashed_password):
            return None

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account"
            )

        return user

    async def login_user(self, login_data: UserLogin) -> dict:
        """Login user and return JWT token"""
        user = await self.authenticate_user(login_data)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user),
        }

    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        username = verify_token(token)
        if username is None:
            raise credentials_exception

        user = await self.user_repo.get_by_username(username)
        if user is None:
            raise credentials_exception

        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self.user_repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.user_repo.get_by_email(email)
