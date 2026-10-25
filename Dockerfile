# syntax=docker/dockerfile:1
# ==============================================================
# Dockerfile
#
# Build from the repository root:   docker build -t network-asset-api .
# (docker compose up --build does this for you.)
#
# CONCEPT — Multi-stage build:
# We use two stages: "builder" and "final".
#
# Stage 1 (builder): Install all dependencies. This stage can
# be large — it may need build tools and pip's working files.
#
# Stage 2 (final): Copy only what we need from the builder.
# The final image is smaller because it has no build tools,
# only the installed packages and your app code.
#
# Why smaller images?
#   - Faster to pull from a registry (less data to download)
#   - Smaller attack surface (fewer tools for an attacker to use)
#   - Cheaper storage in a container registry
# ==============================================================

# ==============================================================
# STAGE 1: Builder
# ==============================================================
FROM python:3.12-slim AS builder

# Set the working directory inside the container
WORKDIR /build

# CONCEPT — Why copy requirements first?
# Docker builds in layers. Each instruction is a layer.
# If requirements.txt has not changed, Docker reuses the
# cached layer and skips pip install. This makes rebuilds
# much faster during development.
# Only when requirements.txt changes does Docker re-install.
COPY requirements.txt .

# Install dependencies into a specific folder (/install)
# so we can copy just this folder in the next stage
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ==============================================================
# STAGE 2: Final image
# ==============================================================
FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE: do not write .pyc files (the code is read-only anyway).
# PYTHONUNBUFFERED: print log lines immediately, so `docker logs` shows them live.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user for security
# CONCEPT — Never run as root in production:
# If an attacker exploits your app, running as root gives them
# full control of the container. A non-root user limits damage.
# A fixed UID (10001) makes file permissions predictable on any host.
RUN useradd --create-home --uid 10001 appuser

# CONCEPT — Where the code lives:
# The Python package is the folder "app/", and every import says
# "from app.core ...". So the code is copied to /srv/app and the
# working directory is its parent, /srv: from there,
# "uvicorn app.main:app" and "alembic upgrade head" both find it.
WORKDIR /srv

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy only what the container needs to run: the migrations and the
# application. Tests, Terraform and docs stay out of the image.
# The files stay owned by root, so the app (running as appuser) can
# read its code but not modify it.
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# Switch to non-root user
USER appuser

# CONCEPT — EXPOSE:
# This does not actually open a port. It is documentation —
# it tells Docker and developers that the app listens on 8000.
# The actual port mapping happens in compose.yaml.
EXPOSE 8000

# CONCEPT — HEALTHCHECK:
# Docker calls GET /health every 10 seconds and marks the container
# "healthy" or "unhealthy" (see `docker ps`). The slim image has no
# curl, so a one-line Python script makes the request instead.
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

# CONCEPT — CMD vs ENTRYPOINT:
# CMD is the default command when the container starts.
# It can be overridden (compose.yaml runs migrations this way).
# We start uvicorn here.
#
# --host 0.0.0.0: Listen on all network interfaces inside
#   the container (not just localhost). Required for Docker.
# --port 8000: The port to listen on inside the container.
# --workers 2: Run 2 worker processes for better performance.
#   In development, use 1. In production, use 2 * CPU_cores + 1.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
