# ==============================================================
# tests/test_incidents.py
# ==============================================================

import pytest


class TestIncidents:

    @pytest.mark.asyncio
    async def test_create_incident_success(self, client, auth_headers):
        """An authenticated user can open an incident."""
        response = await client.post(
            "/incidents/",
            json={
                "title": "Switch down in Server Room 1",
                "description": "Core switch is not responding to ping",
                "severity": "high",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Switch down in Server Room 1"
        assert data["severity"] == "high"
        assert data["status"] == "open"       # Default status
        assert data["reporter_id"] is not None # Set from JWT

    @pytest.mark.asyncio
    async def test_create_incident_unauthenticated_returns_401(self, client):
        """Cannot open an incident without authentication."""
        response = await client.post(
            "/incidents/",
            json={"title": "Some incident", "severity": "low"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_incidents(self, client, auth_headers):
        """Can list all incidents."""
        await client.post(
            "/incidents/",
            json={"title": "Incident 1", "severity": "low"},
            headers=auth_headers,
        )
        response = await client.get("/incidents/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    async def test_filter_incidents_by_status(self, client, auth_headers):
        """Can filter incidents by status."""
        # Create an open incident
        await client.post(
            "/incidents/",
            json={"title": "Open incident", "severity": "medium"},
            headers=auth_headers,
        )

        response = await client.get(
            "/incidents/?status=open",
            headers=auth_headers,
        )
        assert response.status_code == 200
        for incident in response.json():
            assert incident["status"] == "open"

    @pytest.mark.asyncio
    async def test_update_incident_status(self, client, auth_headers):
        """Can update an incident's status."""
        # Create incident
        create_resp = await client.post(
            "/incidents/",
            json={"title": "Network outage", "severity": "critical"},
            headers=auth_headers,
        )
        incident_id = create_resp.json()["id"]

        # Move to in_progress
        update_resp = await client.patch(
            f"/incidents/{incident_id}",
            json={"status": "in_progress"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_resolve_incident_sets_resolved_at(self, client, auth_headers):
        """
        When an incident is resolved, resolved_at is automatically set.
        This tests our business logic in the router.
        """
        create_resp = await client.post(
            "/incidents/",
            json={"title": "Intermittent packet loss", "severity": "medium"},
            headers=auth_headers,
        )
        incident_id = create_resp.json()["id"]

        update_resp = await client.patch(
            f"/incidents/{incident_id}",
            json={
                "status": "resolved",
                "resolution_notes": "Replaced faulty SFP module on port 24",
            },
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["status"] == "resolved"
        assert data["resolution_notes"] == "Replaced faulty SFP module on port 24"

        # resolved_at should be automatically set — not null
        assert data["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_get_nonexistent_incident_returns_404(self, client, auth_headers):
        """Requesting a non-existent incident ID returns 404."""
        response = await client.get("/incidents/99999", headers=auth_headers)
        assert response.status_code == 404