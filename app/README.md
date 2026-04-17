# Network Asset & Incident Management API

A production-grade REST API for IT teams to track infrastructure assets and manage network incidents across multiple tenants.

Built with FastAPI, PostgreSQL, Docker, and deployed to AWS ECS via GitHub Actions CI/CD.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Pydantic v2 |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Authentication | JWT (python-jose) + bcrypt |
| Containerisation | Docker + Docker Compose |
| Cloud | AWS ECS Fargate |
| CI/CD | GitHub Actions |
| Testing | Pytest + httpx |

---

## Features

- JWT authentication with role-based access control (admin / user)
- Full CRUD for IT assets (routers, switches, servers, VMs, cloud instances)
- Incident management with status tracking and automatic resolution timestamps
- Multi-tenant data isolation
- Query filtering and pagination on all list endpoints
- Interactive API documentation at `/docs` (Swagger UI)
- Health check endpoint for container orchestration

---

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Git

### 1. Clone the repository

```bash
git clone https://github.com/your-username/network-asset-api.git
cd network-asset-api
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:
- `POSTGRES_PASSWORD` — choose a strong password
- `SECRET_KEY` — generate one with:
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

### 3. Start all containers

```bash
docker compose up -d
```

This starts three containers:
- **app** — FastAPI on port 8000 (runs migrations automatically)
- **db** — PostgreSQL on port 5432
- **pgadmin** — Database GUI on port 5050

### 4. Verify it is running

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "app": "Network Asset API", "version": "1.0.0"}
```

### 5. Open the interactive docs

Navigate to **http://localhost:8000/docs** in your browser.

You will see the full Swagger UI — register a user, log in, and test every endpoint interactively.

---

## API Overview

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, receive JWT token |

### Assets

| Method | Endpoint | Description |
|---|---|---|
| GET | `/assets/` | List assets (filterable by tenant, type, status) |
| GET | `/assets/{id}` | Get a single asset |
| POST | `/assets/` | Create an asset |
| PATCH | `/assets/{id}` | Update an asset |
| DELETE | `/assets/{id}` | Delete an asset (admin only) |

### Incidents

| Method | Endpoint | Description |
|---|---|---|
| GET | `/incidents/` | List incidents (filterable by status, severity) |
| GET | `/incidents/{id}` | Get a single incident |
| POST | `/incidents/` | Open an incident |
| PATCH | `/incidents/{id}` | Update an incident |
| DELETE | `/incidents/{id}` | Delete an incident (admin only) |

---

## Running Tests

```bash
# Install dependencies locally
pip install -r requirements.txt

# Run all tests
pytest -v
```

Tests use an in-memory SQLite database — no running PostgreSQL needed.

---

## Project Structure

```
network-asset-api/
├── app/
│   ├── core/           # Config, JWT, password hashing
│   ├── db/             # SQLAlchemy engine and session
│   ├── models/         # Database table definitions
│   ├── schemas/        # API request/response shapes
│   ├── routers/        # Endpoint handlers
│   ├── dependencies.py # Shared auth dependencies
│   └── main.py         # App entry point
├── alembic/            # Database migrations
├── tests/              # Pytest test suite
├── .github/workflows/  # CI/CD pipelines
├── Dockerfile
└── docker-compose.yml
```

---

## Useful Commands

```bash
# View running containers
docker compose ps

# View application logs
docker compose logs -f app

# Run database migrations manually
docker compose exec app alembic upgrade head

# Generate a new migration after changing a model
docker compose exec app alembic revision --autogenerate -m "describe your change"

# Access PostgreSQL directly
docker compose exec db psql -U postgres -d network_asset_db

# Stop all containers (data is preserved)
docker compose down

# Stop and delete all data
docker compose down -v
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `POSTGRES_USER` | Yes | — | PostgreSQL username |
| `POSTGRES_PASSWORD` | Yes | — | PostgreSQL password |
| `POSTGRES_HOST` | No | `db` | Database host |
| `POSTGRES_PORT` | No | `5432` | Database port |
| `POSTGRES_DB` | Yes | — | Database name |
| `SECRET_KEY` | Yes | — | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Token expiry in minutes |
| `DEBUG` | No | `False` | Enable SQL query logging |