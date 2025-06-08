from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.features.auth.models import User
from app.features.auth.schemas import UserCreate
from app.core.security import get_password_hash


class UserRepository:
    """Repository for User data access operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        """Create new user"""
        # Hash the password
        hashed_password = get_password_hash(user_data.password)

        # Create user instance
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
        )

        # Add to database
        self.db.add(user)
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError as e:
            await self.db.rollback()
            error_msg = str(e).lower()
            if "users.username" in error_msg:
                raise ValueError("Username already taken")
            elif "users.email" in error_msg:
                raise ValueError("Email already registered")
            else:
                raise ValueError("User creation failed")

    async def update_user(self, user: User) -> User:
        """Update existing user"""
        try:
            await self.db.commit()
            await self.db.refresh(user)
            return user
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Update failed - duplicate email or username")

    async def delete_user(self, user: User) -> bool:
        """Delete user"""
        await self.db.delete(user)
        await self.db.commit()
        return True

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        result = await self.db.execute(select(User.id).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        result = await self.db.execute(select(User.id).where(User.username == username))
        return result.scalar_one_or_none() is not None
