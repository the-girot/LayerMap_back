import pytest

from tests.factories import create_project


@pytest.mark.asyncio
async def test_projects_list_cached(auth_client, authenticated, db_session):
    await create_project(db_session, name="P1")
    resp1 = await auth_client.get("/projects")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1) == 1

    resp2 = await auth_client.get("/projects")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2 == data1
