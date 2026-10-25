# ==============================================================
# app/main.py
#
# WHAT THIS FILE DOES:
#   This is the heart of the application.
#   It creates the FastAPI app instance, registers middleware,
#   mounts all routers, and defines the startup/shutdown behaviour.
#
# When you run: uvicorn app.main:app --reload
#   - "app.main" = the module (app/main.py)
#   - "app"      = the FastAPI() instance inside that module
#   - "--reload" = restart automatically when code changes
# ==============================================================

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import engine, get_db
from app.routers import assets, auth, incidents

# CONCEPT — logging instead of print():
# Log lines carry a level (INFO, WARNING, ERROR) and a logger name,
# and they end up in the same place as uvicorn's own logs.
# "uvicorn.error" is the logger uvicorn uses for its startup messages.
logger = logging.getLogger("uvicorn.error")


# ==============================================================
# CONCEPT — Lifespan context manager:
# Code BEFORE `yield` runs at startup (when the server starts).
# Code AFTER `yield` runs at shutdown (when the server stops).
#
# @asynccontextmanager is a decorator that turns this
# async generator function into a context manager that
# FastAPI can use.
#
# This is the modern FastAPI way (v0.93+). The older way
# used @app.on_event("startup") which is now deprecated.
# ==============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    logger.info("Starting %s v%s (debug=%s)", settings.APP_NAME, settings.APP_VERSION, settings.DEBUG)

    yield  # Application runs here

    # --- Shutdown ---
    # dispose() closes every pooled connection, so PostgreSQL is not
    # left holding connections from a process that no longer exists.
    await engine.dispose()
    logger.info("Database connections closed")


# ==============================================================
# CONCEPT — FastAPI() instance:
# This creates the application object. Every setting here
# appears in the auto-generated Swagger documentation.
#
# docs_url="/docs"   → Interactive Swagger UI
# redoc_url="/redoc" → Alternative ReDoc documentation
#
# In production you would set docs_url=None to hide the docs
# from the public. For development/demo, we keep them open.
# ==============================================================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Network Asset & Incident Management API

A REST API for IT teams to track infrastructure assets and the
network incidents that affect them.

### Features
- **JWT Authentication** with two roles: user and admin
- **Asset Management** — track routers, servers, cloud instances, and more
- **Incident Management** — open, assign, and resolve network incidents
- **Tenants** — every asset records the company or site it belongs to,
  and the asset list can be filtered by it

### How to use
1. Register a user via `POST /auth/register`
2. Click **Authorize** above and log in with your email (as the username) and password
3. All protected endpoints are now accessible; `GET /auth/me` shows who you are
    """,
    lifespan=lifespan,
)


# ==============================================================
# CONCEPT — Middleware:
# Middleware is code that runs on EVERY request and response,
# before and after your endpoint handlers.
# Think of it as a pipeline: Request → Middleware → Endpoint → Middleware → Response
#
# CORSMiddleware handles browser cross-origin security: it tells
# a browser which other websites may call this API from JavaScript.
# The allowed origins come from settings.CORS_ORIGINS, so each
# environment lists exactly its own front end, for example
# CORS_ORIGINS='["https://yourapp.com"]'. The default is none.
#
# Why not allow_origins=["*"]? Combined with allow_credentials=True
# it would let ANY website make authenticated calls on behalf of a
# logged-in user. The tokens here travel in the Authorization header,
# not in cookies, so credentials are not needed for CORS at all.
# ==============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers (including Authorization)
)


# ==============================================================
# CONCEPT — Including routers:
# Each router is a separate module with its own endpoints.
# app.include_router() registers all of a router's endpoints
# with the main application.
#
# The prefix is already set inside each router file,
# so we do not need to add it here.
# ==============================================================
app.include_router(auth.router)
app.include_router(assets.router)
app.include_router(incidents.router)


# ==============================================================
# CONCEPT — Health check endpoint:
# This is a simple GET endpoint that returns {"status": "ok"}.
# It has NO authentication requirement.
#
# Why it matters:
# - Docker uses it to know if the container is healthy
#   (see HEALTHCHECK in the Dockerfile)
# - Load balancers and orchestrators ping it to check if the app is running
# - Monitoring tools use it to alert if the service is down
#
# CONCEPT — Liveness versus readiness:
# /health answers "is the process alive?" and never touches the
# database, so a database outage does not get the app restarted.
# /health/ready answers "can it serve requests?" by running
# SELECT 1. Kubernetes, for example, has a probe for each question.
# ==============================================================
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health/ready", tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ready", "database": "ok"}


# ==============================================================
# Root endpoint — useful as a quick sanity check
# ==============================================================
@app.get("/", tags=["Health"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "health": "/health",
    }
