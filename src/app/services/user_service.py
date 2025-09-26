# app/services/user_service.py
"""
User service module.

This module provides the business logic layer for user operations,
handling authorization, validation, and orchestrating repository calls.
"""
import logging
from typing import Optional, Dict
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timezone
from app.crud.user_crud import user_repository
from app.schemas.user_schema import (
    UserCreate,
    UserResponse,
)
from app.models.user_model import User

from app.core.exception_utils import raise_for_status
from app.core.exceptions import (
    ResourceNotFound,
    NotAuthorized,
    ValidationError,
    ResourceAlreadyExists,
)
from app.core.security import password_manager

logger = logging.getLogger(__name__)


class UserService:
    """Handles all user-related business logic."""

    def __init__(self):
        """
        Initializes the UserService.
        This version has no arguments, making it easy for FastAPI to use,
        while still allowing for dependency injection during tests.
        """
        self.user_repository = user_repository
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _check_authorization(
        self, *, current_user: User, target_user: User, action: str
    ) -> None:
        """
        Central authorization check. An admin can do anything.
        A non-admin can only perform actions on their own account.

        Args:
            current_user: The user performing the action
            target_user: The user being acted upon
            action: Description of the action for error messages

        Raises:
            NotAuthorized: If user lacks permission for the action
        """

        # Users can only modify their own account
        is_not_self = str(current_user.id) != str(target_user.id)
        raise_for_status(
            condition=is_not_self,
            exception=NotAuthorized,
            detail=f"You are not authorized to {action} this user.",
        )

    async def get_user_for_auth(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> Optional[User]:
        """
        A simplified user retrieval method for authentication purposes
        """

        return await self.user_repository.get(db=db, obj_id=user_id)

    async def get_user_by_id(
        self, db: AsyncSession, *, user_id: uuid.UUID, current_user: User
    ) -> Optional[UserResponse]:
        """Retrieve user by it's ID"""

        user = await self.user_repository.get(db=db, obj_id=user_id)
        raise_for_status(
            condition=(user is None),
            exception=ResourceNotFound,
            detail=f"User with id:{user_id} not Found.",
            resource_type="User",
        )

        is_not_self = current_user.id != user.id
        raise_for_status(
            condition=(is_not_self),
            exception=NotAuthorized,
            detail="You are not authorized to view this user's profile.",
        )

        self._logger.debug(f"User {user_id} retrieved by user {current_user.id}")
        return user

    async def create_user(self, db: AsyncSession, *, user_in: UserCreate) -> User:
        """
        Handles the business logic of creating a new user.
        """
        # 1. Check for conflicts
        existing_user = await self.user_repository.get_by_email(db, email=user_in.email)
        raise_for_status(
            condition=existing_user is not None,
            exception=ResourceAlreadyExists,
            detail=f"User with email '{user_in.email}' already exists.",
            resource_type="User",
        )

        # 2. Prepare the user model
        user_dict = user_in.model_dump()
        password = user_dict.pop("password")
        user_dict["hashed_password"] = password_manager.hash_password(password)
        user_dict["created_at"] = datetime.now(timezone.utc)
        user_dict["updated_at"] = datetime.now(timezone.utc)

        user_to_create = User(**user_dict)

        # 3. Delegate creation to the repository
        new_user = await self.user_repository.create(db=db, db_obj=user_to_create)
        self._logger.info(f"New user created: {new_user.email}")

        return new_user

    async def delete_user(
        self, db: AsyncSession, *, user_id_to_delete: uuid.UUID, current_user: User
    ) -> Dict[str, str]:
        """
        Permanently deletes a user account.

        Args:
            db: Database session
            user_id_to_delete: ID of user to delete
            current_user: User making the request

        Returns:
            Dict with success message

        Raises:
            ResourceNotFound: If user doesn't exist
            NotAuthorized: If current user lacks permission
            ValidationError: If trying to delete own account or last admin
        """
        # Input validation

        # 1. Fetch the user to delete
        user_to_delete = await self.user_repository.get(db=db, obj_id=user_id_to_delete)

        raise_for_status(
            condition=(user_to_delete is None),
            exception=ResourceNotFound,
            detail=f"User with id {user_id_to_delete} not Found",
            resource_type="User",
        )

        # 2. Perform authorization check
        self._check_authorization(
            current_user=current_user,
            target_user=user_to_delete,
            action="delete",
        )

        # 3. Business rules validation
        await self._validate_user_deletion(user_to_delete, current_user)

        # 4. Perform the deletion
        await self.user_repository.delete(db=db, obj_id=user_id_to_delete)

        self._logger.warning(
            f"User {user_id_to_delete} permanently deleted by {current_user.id}",
            extra={
                "deleted_user_id": user_id_to_delete,
                "deleter_id": current_user.id,
                "deleted_user_email": user_to_delete.email,
            },
        )

    async def _validate_user_deletion(
        self, user_to_delete: User, current_user: User
    ) -> None:
        """
        Validates user deletion for business rules.

        Args:
            db: Database session
            user_to_delete: User to be deleted
            current_user: User performing the deletion

        Raises:
            ValidationError: If deletion violates business rules
        """
        # Prevent self-deletion
        if current_user.id != user_to_delete.id:
            raise ValidationError("Users cannot delete their own accounts")

        return {"message": "User deleted successfully"}


user_service = UserService()
