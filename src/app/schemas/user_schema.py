import re
from typing import Optional, List
from datetime import datetime, date
import uuid

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)
from app.core.exceptions import ValidationError


class UserBase(BaseModel):
    email: EmailStr = Field(
        ..., description="User's email address", examples=["user@example.com"]
    )


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=6,
        max_length=30,
        description="Strong password",
        examples=["SecurePass123!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValidationError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValidationError(
                "Password must contain at least one special character"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        }
    )


# ======== Response Schemas =========
class UserResponse(UserBase):
    """Basic user response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Registration timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ======== List and Search Schemas =========
class UserListResponse(BaseModel):
    """Response for paginated user list."""

    items: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., ge=0, description="Total number of users")
    page: int = Field(..., ge=1, description="Current page number")
    pages: int = Field(..., ge=0, description="Total number of pages")
    size: int = Field(..., ge=1, le=100, description="Number of items per page")

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.pages

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1


class UserSearchParams(BaseModel):
    """Parameters for searching users."""

    search: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Search in email, username, full name",
    )
    email: Optional[str] = Field(None, description="User's email")
    created_after: Optional[date] = Field(
        None, description="Filter users created after this date"
    )
    created_before: Optional[date] = Field(
        None, description="Filter users created before this date"
    )

    @model_validator(mode="after")
    def validate_date_range(self) -> "UserSearchParams":
        """Ensure date range is valid."""
        if self.created_after and self.created_before:
            if self.created_after > self.created_before:
                raise ValidationError("created_after must be before created_before")
        return self


__all__ = [
    "UserBase",
    "UserCreate",
    # Response schemas
    "UserResponse",
    # List schemas
    "UserListResponse",
    # List and Search Schemas
    "UserSearchParams",
]
