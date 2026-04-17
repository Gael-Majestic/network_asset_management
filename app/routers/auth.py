# ==============================================================
# app/routers/auth.py
#
# WHAT THIS FILE DOES:
#   Handles user registration and login.
#   Endpoints:
#     POST /auth/register  → create a new user account
#     POST /auth/login     → authenticate and receive a JWT token
# ==============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse

# ==============================================================
# CONCEPT — APIRouter:
# APIRouter is like a mini FastAPI app. We define routes on it
# and then register it in main.py with a prefix.
#
# prefix="/auth" means all routes here will be:
#   /auth/register, /auth/login etc.
#
# tags=["Authentication"] groups these endpoints together
# in the Swagger UI documentation — makes it easy to navigate.
# ==============================================================
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    CONCEPT — How a POST endpoint works:
    FastAPI sees the `user_data: UserCreate` parameter and knows
    to read the request body as JSON and validate it against
    the UserCreate schema. If validation fails (e.g. invalid email,
    password too short), FastAPI returns a 422 error automatically.
    Your code never runs if the data is invalid.

    CONCEPT — async/await in a route:
    Every database operation uses `await` because SQLAlchemy is
    running asynchronously. While waiting for PostgreSQL to respond,
    FastAPI can serve other requests. The function is declared
    `async def` to enable this.
    """

    # Step 1: Check if this email is already registered
    # select(User).where(...) is the SQLAlchemy way of writing:
    # SELECT * FROM users WHERE email = 'the_email' LIMIT 1
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        # CONCEPT — HTTP 400 Bad Request:
        # The client made a valid request but with data that
        # violates a business rule (email already taken).
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    # Step 2: Hash the password before storing
    # NEVER store the plain password. hash_password() from
    # security.py turns "hello123" into a bcrypt hash.
    hashed = hash_password(user_data.password)

    # Step 3: Create the User object
    # CONCEPT — ORM object creation:
    # We create a Python object. It is NOT in the database yet.
    # db.add() stages it. The actual INSERT happens when we
    # commit — which get_db() does after the endpoint returns.
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed,
    )

    db.add(new_user)

    # Step 4: Flush so PostgreSQL assigns the auto-increment ID
    # flush() sends the INSERT to PostgreSQL within the current
    # transaction but does NOT commit yet. This gives us the
    # generated ID so we can return it in the response.
    await db.flush()
    await db.refresh(new_user)

    # Step 5: Return the new user
    # FastAPI automatically serializes this User object using
    # the UserResponse schema. Since UserResponse has
    # from_attributes=True, Pydantic reads the object attributes.
    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="Login and receive a JWT access token",
)
async def login(
    # CONCEPT — OAuth2PasswordRequestForm:
    # This is a special FastAPI form class that reads:
    #   username and password from a form body (not JSON).
    # The OAuth2 standard requires form data for the login endpoint.
    # In Swagger UI this shows as actual input fields.
    # We use "username" field but treat it as the email.
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    CONCEPT — The authentication flow:
    1. Client sends username (email) + password as form data
    2. We look up the user by email
    3. We verify the password against the stored hash
    4. If valid, we create and return a JWT token
    5. Client stores the token and sends it with every future request
    """

    # Step 1: Find the user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()

    # Step 2: Verify credentials
    # We use the same generic error message for both "user not found"
    # AND "wrong password". This is intentional security practice —
    # different messages would let attackers discover valid emails.
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Step 3: Check the account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated"
        )

    # Step 4: Create and return the JWT token
    # We embed the user's email as the "sub" (subject) claim.
    # get_current_user() will later decode this to identify the user.
    access_token = create_access_token(data={"sub": user.email})

    return Token(access_token=access_token, token_type="bearer")