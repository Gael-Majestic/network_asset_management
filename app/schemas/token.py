# ==============================================================
# app/schemas/token.py
#
# WHAT THIS FILE DOES:
#   Defines the shape of the JWT token response that the API
#   sends back after a successful login.
#
# CONCEPT — Why a separate file for tokens?
#   The token response is not really about users — it is about
#   the authentication mechanism itself. Keeping it separate
#   makes the codebase cleaner and easier to navigate.
# ==============================================================

from pydantic import BaseModel


class Token(BaseModel):
    """
    What the API returns after a successful login.

    access_token: The JWT string the client must send with
                  every protected request in the Authorization header:
                  Authorization: Bearer eyJhbGciOi...

    token_type:   Always "bearer" — this is the OAuth2 standard
                  name for this type of token. It tells the client
                  how to use the token (put it in the header with
                  the word "Bearer" before it).
    """
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """
    CONCEPT — Internal schema (not exposed to clients):
    This schema is used INSIDE the application, not in HTTP responses.
    After decoding a JWT, we parse the payload into this object
    so we have a typed, validated structure to work with.

    email is Optional because a malformed token might not have a "sub" claim.
    """
    email: str | None = None