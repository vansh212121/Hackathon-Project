"""
Authentication service module.

Handles user authentication, registration, and token management.
"""

import logging
import uuid

from sqlmodel.ext.asyncio.session import AsyncSession
from datetime import datetime, timezone
from app.crud.user_crud import user_repository
from app.services.rate_limit_service import rate_limit_service

from app.schemas.token_schema import TokenResponse
from app.models.user_model import User
from app.core.security import token_manager, TokenType, password_manager

from app.core.exceptions import (
    InvalidCredentials,
    InternalServerError,
)


logger = logging.getLogger(__name__)


class AuthService:
    """
    Service class for authentication operations.

    Handles user registration, login, logout, password reset,
    and email verification with comprehensive security features.
    """

    def __init__(self):
        self.user_repository = user_repository
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def create_token_pair(self, *, user: User) -> TokenResponse:
        """
        Creates and returns a new access and refresh token pair for a user.
        This is a helper method used by login and refresh flows.
        """
        access_token = token_manager.create_token(
            subject=str(user.id), token_type=TokenType.ACCESS
        )
        refresh_token = token_manager.create_token(
            subject=str(user.id), token_type=TokenType.REFRESH
        )
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def login(
        self, db: AsyncSession, *, email: str, password: str, client_ip: str
    ) -> TokenResponse:
        """The core authentication workflow."""

        # 1. Brute-force protection check
        if await rate_limit_service.is_auth_rate_limited(client_ip):
            raise InvalidCredentials(
                detail="Too many failed login attempts. Please try again later."
            )

        # 2. Fetch the user from databse
        user = await user_repository.get_by_email(db=db, email=email)

        # 3. Verify the user and password
        password_is_valid = user and password_manager.verify_password(
            password, user.hashed_password
        )

        if not password_is_valid:
            await rate_limit_service.record_failed_auth_attempt(client_ip)
            raise InvalidCredentials()

        # 4. On successful login, clear any previous failed attempts
        await rate_limit_service.clear_failed_auth_attempts(client_ip)

        # 6. Check if the password needs to be re-hashed with stronger parameters
        if password_manager.upgrade_hash_if_needed(password, user.hashed_password):
            user.hashed_password = password_manager.hash_password(password)
            db.add(user)
            await db.commit()
            logger.info(f"Password re-hashed for user {user.id}")

        # Use the helper to create the token pair
        token_response = self.create_token_pair(user=user)

        logger.info(f"User {user.id} logged in successfully.")
        return token_response

    async def refresh_token(
        self, db: AsyncSession, *, refresh_token: str
    ) -> TokenResponse:
        """
        Refreshes a user's session using a valid refresh token.
        Implements Refresh Token Rotation for enhanced security.
        """
        # 1. Verify the refresh token. This also checks the blacklist.
        payload = await token_manager.verify_token(
            refresh_token, expected_type=TokenType.REFRESH
        )
        user_id = uuid.UUID(payload.get("sub"))

        # 2. Fetch the user from the database
        user = await user_repository.get(db, obj_id=user_id)

        # 3. Revoke the old refresh token (one-time use)
        revoked_successfully = await token_manager.revoke_token(
            refresh_token, reason="Token refreshed"
        )

        if not revoked_successfully:
            raise InternalServerError(
                detail="Could not refresh token. Please try logging in again."
            )

        # 4. Issue a new token pair
        new_token_response = self.create_token_pair(user=user)

        logger.info(f"Token refreshed for user {user.id}")
        return new_token_response

    async def logout(self, *, access_token: str, refresh_token: str) -> None:
        """
        Logs a user out by revoking their current access and refresh tokens.
        """
        await token_manager.revoke_token(access_token, reason="User logout")
        await token_manager.revoke_token(refresh_token, reason="User logout")
        logger.info("User logged out successfully.")

    async def revoke_all_user_tokens(self, db: AsyncSession, *, user: User):
        """
        Revokes all tokens for a user by updating the tokens_valid_from_utc timestamp.
        """
        # Set the revocation timestamp to the current time
        await user_repository.update(
            db=db,
            user=user,
            fields_to_update={"tokens_valid_from_utc": datetime.now(timezone.utc)},
        )
        self._logger.info(f"All tokens revoked for user {user.id}")


auth_service = AuthService()
