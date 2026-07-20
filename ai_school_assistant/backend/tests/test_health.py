"""Smoke tests for the M0 application skeleton."""

import httpx
import pytest

from app.main import create_app


@pytest.fixture
def client() -> httpx.AsyncClient:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_healthz(client: httpx.AsyncClient) -> None:
    async with client:
        response = await client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]


async def test_readyz(client: httpx.AsyncClient) -> None:
    async with client:
        response = await client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_unknown_route_is_404(client: httpx.AsyncClient) -> None:
    async with client:
        response = await client.get("/nope")
    assert response.status_code == 404
