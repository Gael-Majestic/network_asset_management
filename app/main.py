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

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import assets, auth, incidents


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
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    print("Database connection pool initialized.")
    print("API docs available at: http://localhost:8000/docs")

    yield  # Application runs here

    # --- Shutdown ---
    print("Shutting down. Closing database connections.")


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

A production-grade REST API for IT teams to track infrastructure assets
and manage network incidents across multiple tenants.

### Features
- **JWT Authentication** with role-based access control
- **Asset Management** — track routers, servers, cloud instances, and more
- **Incident Management** — open, assign, and resolve network incidents
- **Multi-tenant** — each company's data is isolated

### How to use
1. Register a user via `POST /auth/register`
2. Login via `POST /auth/login` to receive a JWT token
3. Click **Authorize** above and enter: `Bearer your_token_here`
4. All protected endpoints are now accessible
    """,
    lifespan=lifespan,
)


# ==============================================================
# CONCEPT — Middleware:
# Middleware is code that runs on EVERY request and response,
# before and after your endpoint handlers.
# Think of it as a pipeline: Request → Middleware → Endpoint → Middleware → Response
#
# CORSMiddleware handles browser cross-origin security.
# allow_origins=["*"] allows ALL origins — fine for development.
# In production, replace with your actual frontend domain:
# allow_origins=["https://yourapp.com"]
# ==============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins (development)
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers
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
# - AWS ECS/load balancers ping it to check if the app is running
# - Monitoring tools use it to alert if the service is down
#
# Every production API must have a /health endpoint.
# ==============================================================
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


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