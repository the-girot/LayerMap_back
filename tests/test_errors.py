import pytest


@pytest.mark.anyio
async def test_not_found_project(client):
    resp = await client.get("/projects/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Проект не найден"


@pytest.mark.anyio
async def test_validation_error_pagination(client):
    resp = await client.get("/projects/1/rpi-mappings", params={"skip": -1, "limit": 200})
    assert resp.status_code == 422
