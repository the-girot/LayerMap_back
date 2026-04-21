import pytest

from tests.factories import create_project, create_source


@pytest.mark.anyio
async def test_create_source(client, db_session):
    project = await create_project(db_session)
    resp = await client.post(
        f"/projects/{project.id}/sources",
        json={
            "name": "Основная БД",
            "description": "Описание",
            "type": "DB",
            "row_count": 0,
            "mapping_table_id": None,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == project.id
    assert data["type"] == "DB"


@pytest.mark.anyio
async def test_get_sources_list(client, db_session):
    project = await create_project(db_session)
    await create_source(db_session, project, name="S1")
    await create_source(db_session, project, name="S2")

    resp = await client.get(f"/projects/{project.id}/sources")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert {s["name"] for s in data} == {"S1", "S2"}


@pytest.mark.anyio
async def test_source_404_for_wrong_project(client, db_session):
    p1 = await create_project(db_session, name="P1")
    p2 = await create_project(db_session, name="P2")
    s1 = await create_source(db_session, p1, name="S1")

    resp = await client.get(f"/projects/{p2.id}/sources/{s1.id}")
    assert resp.status_code == 404
