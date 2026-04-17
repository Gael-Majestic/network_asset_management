# ==============================================================
# app/schemas/user.py
#
# WHAT THIS FILE DOES:
#   Defines the shapes of data going INTO and coming OUT OF
#   the API for user-related operations.
#
# CONCEPT — Pydantic BaseModel:
#   Every schema inherits from BaseModel. Pydantic reads the
#   type annotations and automatically:
#     - Validates incoming data (wrong type = 422 error with details)
#     - Converts types where possible (e.g. "30" string → 30 int)
#     - Generates JSON schema for Swagger documentation
#   You get all of this for free just by declaring types.
# ==============================================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """
    Fields shared by all user schemas.
    We never instantiate this directly — it is a base for others.

    CONCEPT — EmailStr:
    This is a special Pydantic type that validates email format.
    If someone sends "not-an-email", Pydantic rejects it with
    a clear validation error before your code ever runs.
    You get this type by installing: pip install pydantic[email]
    (already included via fastapi install)
    """
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """
    Schema for POST /auth/register
    The client sends: email, full_name (optional), password

    CONCEPT — Field() with constraints:
    Field() lets you add validation rules AND documentation.
    min_length=8 means Pydantic rejects passwords shorter than 8 chars.
    The description appears in the Swagger UI documentation.
    """
    password: str = Field(
        ...,              # ... means this field is REQUIRED (no default)
        min_length=8,
        description="Password must be at least 8 characters"
    )


class UserUpdate(BaseModel):
    """
    Schema for PATCH /users/{id}
    All fields are Optional because the client may update
    only one field at a time without sending the others.

    CONCEPT — Optional[str] = None:
    Optional[str] is shorthand for Union[str, None].
    It means the field can be a string OR None.
    Setting the default to None means if not sent, it is None.
    In the router, we check: if field is not None, update it.
    """
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)


class UserResponse(UserBase):
    """
    Schema for API responses — what the API sends BACK to the client.

    Notice what is NOT here: password, hashed_password.
    We never expose those in a response.

    CONCEPT — model_config with from_attributes:
    By default, Pydantic only reads from dictionaries.
    Our SQLAlchemy models are Python objects, not dicts.
    Setting from_attributes=True tells Pydantic:
    "You can also read from object attributes."
    This allows: UserResponse.model_validate(user_orm_object)
    Without this, you would get an error trying to serialize
    a SQLAlchemy object.

    This used to be called `orm_mode = True` in Pydantic v1.
    In Pydantic v2 it is `from_attributes = True`.
    """
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}