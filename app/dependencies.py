# ==============================================================
# app/dependencies.py
#
# WHAT THIS FILE DOES:
#   Defines reusable "dependencies" — functions that FastAPI
#   calls automatically and injects into your endpoints.
#
#   Think of these as middleware for individual endpoints.
#   Instead of copying the same auth logic into every route,
#   you write it once here and declare it where needed.
#
# The two dependencies here are:
#   get_db          → provides a database session
#   get_current_user → reads the JWT and returns the logged-in user
# ==============================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.user import User

# ==============================================================
# CONCEPT — OAuth2PasswordBearer:
# This object does two things:
#   1. It tells FastAPI's Swagger UI (/docs) that this API
#      uses OAuth2 Bearer token authentication. This is what
#      creates the "Authorize" button in the Swagger UI.
#   2. It extracts the token from the Authorization header
#      of every incoming request automatically.
#
# tokenUrl="/auth/login" tells Swagger where to send
# login requests to get a token. This makes the Swagger UI
# interactive — you can log in and test protected endpoints
# directly from the browser.
#
# When an endpoint declares:
#   token: str = Depends(oauth2_scheme)
# FastAPI automatically extracts the Bearer token string
# from the Authorization header and passes it in.
# ==============================================================
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    CONCEPT — Chained dependencies:
    This dependency itself has dependencies: oauth2_scheme and get_db.
    FastAPI resolves them in order — it extracts the token,
    opens a DB session, then calls this function with both.
    Dependencies can depend on other dependencies. This is
    called "dependency chaining" and keeps code very modular.

    What this function does step by step:
      1. Receives the JWT token string (extracted by oauth2_scheme)
      2. Decodes it to get the user's email
      3. Queries the database for that user
      4. Returns the User object if everything is valid
      5. Raises HTTP 401 if anything is wrong

    Any endpoint that declares:
      current_user: User = Depends(get_current_user)
    is automatically protected. Unauthenticated requests
    never reach the endpoint body.
    """

    # CONCEPT — HTTPException:
    # This is how FastAPI returns error responses.
    # We define it here to reuse it in multiple places below.
    # status.HTTP_401_UNAUTHORIZED = 401
    # WWW-Authenticate: Bearer tells the client what
    # authentication scheme to use (standard HTTP behaviour).
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Step 1: Decode the token and extract the email
    email = decode_access_token(token)
    if email is None:
        raise credentials_exception

    # Step 2: Look up the user in the database
    # CONCEPT — SQLAlchemy async query:
    # select(User) builds a SELECT statement.
    # .where() adds a WHERE clause.
    # await db.execute() runs it asynchronously.
    # .scalar_one_or_none() returns one result or None.
    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    # Step 3: Make sure the user exists
    if user is None:
        raise credentials_exception

    # Step 4: Make sure the account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated"
        )

    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    CONCEPT — Layered authorization:
    This dependency builds ON TOP of get_current_user.
    First it ensures the user is authenticated (via get_current_user),
    then it checks if they are an admin.

    This is role-based access control (RBAC) done simply.
    Endpoints that should only be accessible to admins declare:
      current_user: User = Depends(get_current_admin_user)

    Non-admin users get a 403 Forbidden response automatically.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required for this action"
        )
    return current_user