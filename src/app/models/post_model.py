# app/models/user_model.py
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING, List
from sqlalchemy import Enum as SAEnum
from sqlalchemy import func, Column, DateTime, Text
from sqlalchemy.dialects.postgresql import (
    UUID as PG_UUID,
)
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .user_model import User


class Status(str, Enum):

    SCHEDULED = "scheduled"
    SUCCESSFULL = "successfull"
    FAILED = "FAILED"


class Post(SQLModel, table=True):

    __tablename__ = "posts"

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
    content: str = Field(
        sa_column=Column(
            Text,
            nullable=False,
        ),
    )
    status: Status = Field(
        sa_column=Column(SAEnum(Status), nullable=False, index=True),
        default=Status.SCHEDULED,
    )
    scheduled_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True, index=True),
    )
    published_at: Optional[datetime] = Field(default=None)

    # RELATIONSHIPS
    user: "User" = Relationship(back_populates="posts")

    # --- Computed properties (data-focused) ---
    def __repr__(self) -> str:
        return f"<Post(id='{self.id}', user_id='{self.user_id}')>"
