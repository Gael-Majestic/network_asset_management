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
        assert data["status"] == "open"  # Default status
        assert data["reporter_id"] is not None  # Set from JWT

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


class TestIncidentRules:
    async def test_incident_for_missing_asset_returns_404(self, client, auth_headers):
        """A foreign key to nothing is a client error, not a 500."""
        response = await client.post(
            "/incidents/", json={"title": "Link down", "asset_id": 99999}, headers=auth_headers
        )
        assert response.status_code == 404

    async def test_reopening_clears_resolved_at(self, client, auth_headers):
        created = await client.post("/incidents/", json={"title": "Packet loss"}, headers=auth_headers)
        url = f"/incidents/{created.json()['id']}"
        resolved = await client.patch(url, json={"status": "resolved"}, headers=auth_headers)
        assert resolved.json()["resolved_at"] is not None
        reopened = await client.patch(url, json={"status": "open"}, headers=auth_headers)
        assert reopened.json()["resolved_at"] is None

    async def test_closing_keeps_the_resolution_time(self, client, auth_headers):
        created = await client.post("/incidents/", json={"title": "DNS slow"}, headers=auth_headers)
        url = f"/incidents/{created.json()['id']}"
        resolved = await client.patch(url, json={"status": "resolved"}, headers=auth_headers)
        closed = await client.patch(url, json={"status": "closed"}, headers=auth_headers)
        assert closed.json()["resolved_at"] == resolved.json()["resolved_at"]

    async def test_deleting_an_asset_keeps_its_incidents(self, client, auth_headers, make_user):
        """The incident history stays; its link to the deleted asset is cleared."""
        asset = await client.post(
            "/assets/", json={"name": "AP-3", "asset_type": "access_point", "tenant": "Site C"}, headers=auth_headers
        )
        incident = await client.post(
            "/incidents/", json={"title": "AP offline", "asset_id": asset.json()["id"]}, headers=auth_headers
        )
        admin = await make_user("admin@example.com", is_admin=True)
        assert (await client.delete(f"/assets/{asset.json()['id']}", headers=admin)).status_code == 204
        response = await client.get(f"/incidents/{incident.json()['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["asset_id"] is None

    @pytest.mark.parametrize("field", ["title", "severity", "status"])
    async def test_patch_null_for_required_field_returns_422(self, client, auth_headers, field):
        created = await client.post("/incidents/", json={"title": "Jitter"}, headers=auth_headers)
        response = await client.patch(f"/incidents/{created.json()['id']}", json={field: None}, headers=auth_headers)
        assert response.status_code == 422
