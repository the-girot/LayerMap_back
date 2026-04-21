import pytest

from tests.factories import create_project


@pytest.mark.anyio
async def test_create_project(client):
    resp = await client.post(
        "/projects",
        json={"name": "Проект А", "description": "Описание", "status": "active"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] > 0
    assert data["name"] == "Проект А"
    assert data["status"] == "active"


@pytest.mark.anyio
async def test_get_projects_list(client, db_session):
    await create_project(db_session, name="Проект А")
    await create_project(db_session, name="Проект B")

    resp = await client.get("/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert {p["name"] for p in data} == {"Проект А", "Проект B"}


@pytest.mark.anyio
async def test_get_project_by_id(client, db_session):
    project = await create_project(db_session, name="Проект А")
    resp = await client.get(f"/projects/{project.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == project.id
    assert data["name"] == "Проект А"


@pytest.mark.anyio
async def test_update_project(client, db_session):
    project = await create_project(db_session, name="Проект А")
    resp = await client.patch(
        f"/projects/{project.id}",
        json={"name": "Проект A+", "status": "active"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Проект A+"


@pytest.mark.anyio
async def test_delete_project(client, db_session):
    project = await create_project(db_session, name="Проект А")
    resp = await client.delete(f"/projects/{project.id}")
    assert resp.status_code == 204

    resp2 = await client.get(f"/projects/{project.id}")
    assert resp2.status_code == 404
    assert resp2.json()["detail"] == "Проект не найден"


@pytest.mark.anyio
async def test_project_name_unique_violation(client, db_session):
    await create_project(db_session, name="Проект А")
    resp = await client.post(
        "/projects",
        json={"name": "Проект А", "description": "Описание", "status": "active"},
    )
    assert resp.status_code == 409
    assert "уже существует" in resp.json()["detail"]
