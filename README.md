# Network Asset & Incident Management API

A REST API for IT teams to track infrastructure assets (routers, switches, servers, virtual machines) and
the network incidents that affect them. It uses FastAPI with async SQLAlchemy and PostgreSQL, Alembic
migrations, JWT authentication with admin and user roles, and a pytest suite. Docker Compose runs it
locally; Terraform describes a development VM on AWS.

- [`app/`](app/): the API, its tests and the Docker setup. Start with [`app/README.md`](app/README.md).
- [`infrastructure/`](infrastructure/): Terraform for the development VM and a step-by-step
  [`SETUP_GUIDE.sh`](infrastructure/SETUP_GUIDE.sh). Administrative ports are open only to the address
  given in `admin_cidr`, and no password is stored in the code.

**Status.** A personal project, still in progress. The GitHub Actions workflows in `app/.github/` are
drafts and are not active yet.
