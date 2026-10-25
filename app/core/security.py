# ==============================================================
# app/core/security.py
#
# WHAT THIS FILE DOES:
#   1. Hashes passwords before storing them in the database
#   2. Verifies a plain password against a stored hash
#   3. Creates JWT access tokens when a user logs in
#   4. Decodes JWT tokens to identify who is making a request
#
# The libraries are the ones the FastAPI security tutorial uses:
# pwdlib (Argon2) for passwords and PyJWT for tokens.
# https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# ==============================================================

from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

# ==============================================================
# CONCEPT — PasswordHash.recommended():
# This object does the password hashing. "recommended" picks
# Argon2, the winner of the Password Hashing Competition and the
# first choice in the OWASP Password Storage Cheat Sheet. Argon2
# is deliberately slow and memory-hungry, which makes guessing
# passwords from a stolen database very expensive.
# ==============================================================
password_hash = PasswordHash.recommended()

# A hash of a throwaway password. When someone logs in with an
# email that does not exist, we still verify the password against
# this hash, so the response takes as long as for a real account.
# Without it, an attacker could tell which emails are registered
# just by timing the login endpoint.
DUMMY_HASH = password_hash.hash("dummy-password-for-timing")

# The algorithm used to sign JWT tokens.
# HS256 = HMAC with SHA-256. A widely trusted standard.
ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    """
    Takes a plain text password and returns its Argon2 hash.

    CONCEPT — What a password hash with a salt does:
    The hasher adds a random "salt" to the password before hashing.
    A salt is a random string that is different for every user.
    This means two users with the same password will have
    completely different hashes. This defeats "rainbow table"
    attacks where hackers pre-compute hashes for common passwords.

    Example:
        hash_password("hello123")
        → "$argon2id$v=19$m=65536,t=3,p=4$..."
    The hash records the algorithm, its cost settings and the salt,
    so it can be verified later without storing anything else.
    """
    return password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain password matches a stored hash.
    Returns True if they match, False if they do not.

    CONCEPT — How verification works without reversing:
    The hasher reads the salt and settings from the stored hash,
    re-hashes the plain password WITH that same salt, and compares
    the result. If they match, the password is correct.

    Example:
        verify_password("hello123", "$argon2id$...")  → True
        verify_password("wrongpass", "$argon2id$...") → False
    """
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT token containing the given data.

    CONCEPT — What goes into the token:
    The `data` dict is called the "payload". We always include:
    - "sub" (subject): the user's identifier, conventionally their email
    - "exp" (expiration): a timestamp after which the token is invalid

    The token is then SIGNED using our SECRET_KEY. Anyone can
    READ the payload (it is base64 encoded, not encrypted), but
    no one can MODIFY it without invalidating the signature.
    This is why you never put sensitive data (passwords, credit
    cards) in a JWT — only identifiers.

    Args:
        data: Dictionary to encode into the token.
              Usually {"sub": user.email}
        expires_delta: How long until the token expires.
                       If not given, uses the value from settings.

    Returns:
        A JWT token string.
    """
    # Make a copy so we do not modify the original dict
    to_encode = data.copy()

    # Calculate when this token should expire
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add expiration time to the payload
    to_encode.update({"exp": expire})

    # Sign and encode the token using our secret key
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    """
    Decodes a JWT token and returns the subject (user email).
    Returns None if the token is invalid or expired.

    CONCEPT — What "decoding" means:
    jwt.decode() does two things at once:
    1. Verifies the SIGNATURE using SECRET_KEY.
       If someone tampered with the token, this fails.
    2. Checks the EXPIRATION timestamp.
       If the token is expired, this raises an exception.

    Only if both checks pass do we get the payload back.

    Args:
        token: The JWT string sent by the user in the request header

    Returns:
        The email (subject) stored in the token, or None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        # "sub" is the standard JWT claim for "subject" — who this token belongs to
        email: Optional[str] = payload.get("sub")
        return email
    except InvalidTokenError:
        # InvalidTokenError covers: expired tokens, invalid signature, malformed tokens
        return None
