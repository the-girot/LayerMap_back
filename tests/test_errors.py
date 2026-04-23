import pytest

from tests.factories import create_project


@pytest.mark.anyio
async def test_not_found_project(auth_client, authenticated):
    resp = await auth_client.get("/projects/9999")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Проект не найден"


@pytest.mark.anyio
async def test_validation_error_pagination(auth_client, authenticated, db_session):
    project = await create_project(db_session)
    resp = await auth_client.get(
        f"/projects/{project.id}/rpi-mappings",
        params={"skip": -1, "limit": 200},
    )
    assert resp.status_code == 422
