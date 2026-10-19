# ==============================================================
# Dockerfile
#
# CONCEPT — Multi-stage build:
# We use two stages: "builder" and "final".
#
# Stage 1 (builder): Install all dependencies. This stage can
# be large — it has build tools, compilers, etc.
#
# Stage 2 (final): Copy only what we need from the builder.
# The final image is smaller because it has no build tools,
# only the installed packages and your app code.
#
# Why smaller images?
#   - Faster to pull from a registry (less data to download)
#   - Smaller attack surface (fewer tools for an attacker to use)
#   - Cheaper storage in AWS ECR
# ==============================================================

# ==============================================================
# STAGE 1: Builder
# ==============================================================
FROM python:3.12-slim AS builder

# Set the working directory inside the container
WORKDIR /app

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

# Create a non-root user for security
# CONCEPT — Never run as root in production:
# If an attacker exploits your app, running as root gives them
# full control of the container. A non-root user limits damage.
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Change ownership to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# CONCEPT — EXPOSE:
# This does not actually open a port. It is documentation —
# it tells Docker and developers that the app listens on 8000.
# The actual port mapping happens in docker-compose.yml.
EXPOSE 8000

# CONCEPT — CMD vs ENTRYPOINT:
# CMD is the default command when the container starts.
# It can be overridden. We start uvicorn here.
#
# --host 0.0.0.0: Listen on all network interfaces inside
#   the container (not just localhost). Required for Docker.
# --port 8000: The port to listen on inside the container.
# --workers 2: Run 2 worker processes for better performance.
#   In development, use 1. In production, use 2 * CPU_cores + 1.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

