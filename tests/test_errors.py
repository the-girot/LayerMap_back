import pytest

from tests.factories import create_project


@pytest.mark.anyio
async def test_not_found_project(client):
    resp = await client.get("/projects/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Проект не найден"


@pytest.mark.anyio
async def test_validation_error_pagination(client, db_session):  # ← добавить db_session
    project = await create_project(db_session)  # ← создать проект
    resp = await client.get(
        f"/projects/{project.id}/rpi-mappings",  # ← использовать реальный id
        params={"skip": -1, "limit": 200},
    )
    assert resp.status_code == 422
