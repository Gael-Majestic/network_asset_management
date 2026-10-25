# ==============================================================
# tests/test_health.py
#
# The health endpoints need no login: Docker, load balancers and
# monitoring call them without credentials.
# ==============================================================


async def test_liveness(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_readiness_checks_the_database(client):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}
