# ==============================================================
# app/schemas/validators.py
#
# WHAT THIS FILE DOES:
#   Validation rules shared by more than one schema.
# ==============================================================

import ipaddress
from typing import Annotated

from pydantic import AfterValidator, BaseModel


def _normalise_ip(value: str) -> str:
    """
    CONCEPT — AfterValidator:
    Pydantic first checks that the value is a string, then calls
    this function with it. Raising ValueError turns into a normal
    422 validation error for the client; the returned value is
    what gets stored.

    ipaddress.ip_address() accepts IPv4 ("10.0.0.1") and IPv6
    ("2001:db8::1") and rejects anything else ("10.0.0.300",
    "router-1"). str() gives the canonical spelling, so
    "2001:DB8:0:0::1" is stored as "2001:db8::1".
    """
    return str(ipaddress.ip_address(value.strip()))


# CONCEPT — Annotated types:
# Annotated[str, AfterValidator(...)] is "a str, plus this rule".
# Every schema that uses IPAddressStr gets the same validation,
# and the column in the database stays a plain string.
IPAddressStr = Annotated[str, AfterValidator(_normalise_ip)]


def reject_nulls(model: BaseModel, fields: tuple[str, ...]) -> None:
    """
    CONCEPT — "Not sent" versus "sent as null" in a PATCH:
    In an update schema every field is Optional, so the client can
    send only what changes. But Optional also lets the client send
    {"name": null}, which would try to write NULL into a NOT NULL
    column and make the database fail with a 500 error.

    model_fields_set holds the fields the client actually sent.
    A field that was sent AND is None is rejected here with a clear
    422 error; a field that was simply left out is fine.
    """
    for field in fields:
        if field in model.model_fields_set and getattr(model, field) is None:
            raise ValueError(f"{field} cannot be null")
