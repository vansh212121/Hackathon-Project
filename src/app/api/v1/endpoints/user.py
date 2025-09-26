import logging

from typing import Dict
from fastapi import APIRouter, Depends, status, Query

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings
from app.schemas.user_schema import UserResponse
from app.models.user_model import User
from app.db.session import get_session
from app.utils.deps import (
    get_current_user,
    rate_limit_api,
)
from app.services.user_service import user_service


logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["User"],
    prefix=f"{settings.API_V1_STR}/users",
)


# ------ Current User Operations ------
@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get profile information for the authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def get_my_profile(
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.delete(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=Dict[str, str],
    summary="Delete current user profile",
    description="Delete profile information for the authenticated user",
    dependencies=[Depends(rate_limit_api)],
)
async def delete_my_profile(
    *,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete current user's profile"""

    await user_service.delete_user(
        db=db, user_id_to_delete=current_user.id, current_user=current_user
    )

    return {"message": "User deleted successfully!"}
