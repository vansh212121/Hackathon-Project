# app/models/user_model.py
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
from sqlalchemy import Enum as SAEnum
from sqlalchemy import func, Column, Text, DateTime
from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
)
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .user_model import User


class Platform(str, Enum):
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"


class SocialAccount(SQLModel, table=True):

    __tablename__ = "socials"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            PG_UUID(as_uuid=True),
            server_default=func.gen_random_uuid(),
            primary_key=True,
            index=True,
            nullable=False,
        ),
    )
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True, nullable=False)
    platform: Platform = Field(
        sa_column=Column(SAEnum(Platform), nullable=False, index=True),
        default=Platform.LINKEDIN,
    )
    platform_user_id: str = Field(nullable=False, index=True)
    access_token: str = Field(sa_column=Column(Text, nullable=False))
    refresh_token: str = Field(sa_column=Column(Text, nullable=False))
    token_expires_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    )

    # RELATIONSHIPS
    user: "User" = Relationship(back_populates="socials")

    # --- Computed properties (data-focused) ---
    def __repr__(self) -> str:
        return f"<SocialAccount(id='{self.id}', user_id='{self.user_id}')>"
