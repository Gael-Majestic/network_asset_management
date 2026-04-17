# ==============================================================
# tests/test_assets.py
#
# Tests all asset endpoints:
#   - Create, list, get, update, delete
#   - Unauthenticated access is rejected
#   - Non-owners cannot update other users' assets
# ==============================================================

import pytest


class TestAssets:

    @pytest.mark.asyncio
    async def test_create_asset_success(self, client, auth_headers):
        """An authenticated user can create an asset."""
        response = await client.post(
            "/assets/",
            json={
                "name": "Core Router - Site A",
                "asset_type": "router",
                "status": "active",
                "location": "Server Room 1",
                "ip_address": "192.168.1.1",
                "tenant": "Kamoa Copper",
                "description": "Main border router",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Core Router - Site A"
        assert data["asset_type"] == "router"
        assert data["tenant"] == "Kamoa Copper"
        # owner_id is set from the JWT, not the request body
        assert "owner_id" in data
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_asset_unauthenticated_returns_401(self, client):
        """Creating an asset without a token returns 401."""
        response = await client.post(
            "/assets/",
            json={
                "name": "Some Router",
                "asset_type": "router",
                "tenant": "Test Corp",
            },
            # No auth_headers — no token
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_assets(self, client, auth_headers):
        """Authenticated user can list assets."""
        # Create two assets first
        for i in range(2):
            await client.post(
                "/assets/",
                json={
                    "name": f"Switch {i}",
                    "asset_type": "switch",
                    "tenant": "Test Corp",
                },
                headers=auth_headers,
            )

        response = await client.get("/assets/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    @pytest.mark.asyncio
    async def test_list_assets_filter_by_tenant(self, client, auth_headers):
        """Filtering by tenant returns only matching assets."""
        # Create asset for tenant A
        await client.post(
            "/assets/",
            json={"name": "Router A", "asset_type": "router", "tenant": "Company A"},
            headers=auth_headers,
        )
        # Create asset for tenant B
        await client.post(
            "/assets/",
            json={"name": "Router B", "asset_type": "router", "tenant": "Company B"},
            headers=auth_headers,
        )

        response = await client.get(
            "/assets/?tenant=Company A",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        # All returned assets must belong to Company A
        for asset in data:
            assert asset["tenant"] == "Company A"

    @pytest.mark.asyncio
    async def test_get_single_asset(self, client, auth_headers):
        """Can retrieve a specific asset by ID."""
        # Create an asset
        create_response = await client.post(
            "/assets/",
            json={"name": "Firewall X", "asset_type": "firewall", "tenant": "Corp"},
            headers=auth_headers,
        )
        asset_id = create_response.json()["id"]

        # Retrieve it
        response = await client.get(f"/assets/{asset_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == asset_id
        assert response.json()["name"] == "Firewall X"

    @pytest.mark.asyncio
    async def test_get_nonexistent_asset_returns_404(self, client, auth_headers):
        """Requesting an asset ID that does not exist returns 404."""
        response = await client.get("/assets/99999", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_asset(self, client, auth_headers):
        """Owner can update their asset."""
        # Create
        create_resp = await client.post(
            "/assets/",
            json={"name": "Old Name", "asset_type": "server", "tenant": "Corp"},
            headers=auth_headers,
        )
        asset_id = create_resp.json()["id"]

        # Update only the name and status
        update_resp = await client.patch(
            f"/assets/{asset_id}",
            json={"name": "New Name", "status": "maintenance"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["name"] == "New Name"
        assert data["status"] == "maintenance"
        # Other fields should be unchanged
        assert data["asset_type"] == "server"

    @pytest.mark.asyncio
    async def test_delete_asset_as_non_admin_returns_403(self, client, auth_headers):
        """
        A regular (non-admin) user cannot delete assets.
        Delete is restricted to admins only.
        """
        create_resp = await client.post(
            "/assets/",
            json={"name": "To Delete", "asset_type": "switch", "tenant": "Corp"},
            headers=auth_headers,
        )
        asset_id = create_resp.json()["id"]

        delete_resp = await client.delete(
            f"/assets/{asset_id}",
            headers=auth_headers,  # Regular user token
        )
        # Regular users get 403 Forbidden
        assert delete_resp.status_code == 403