import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    create_source_column,
    create_source_table,
    create_project,
    create_source,
)


@pytest.mark.anyio
async def test_create_source_table(auth_client: AsyncClient, db_session: AsyncSession):
    project = await create_project(db_session)
    source = await create_source(db_session, project)

    resp = await auth_client.post(
        f"/projects/{project.id}/sources/{source.id}/tables",
        json={
            "name": "Таблица клиентов",
            "description": "Описание",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["source_id"] == source.id


@pytest.mark.anyio
async def test_list_source_tables_with_columns(
    auth_client: AsyncClient, db_session: AsyncSession
):
    project = await create_project(db_session)
    source = await create_source(db_session, project)
    st = await create_source_table(db_session, source)
    await create_source_column(db_session, st, name="customer_id")

    resp = await auth_client.get(f"/projects/{project.id}/sources/{source.id}/tables")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["columns"][0]["name"] == "customer_id"


@pytest.mark.anyio
async def test_create_source_column_requires_formula_if_calculated(
    auth_client: AsyncClient, db_session: AsyncSession
):
    project = await create_project(db_session)
    source = await create_source(db_session, project)
    st = await create_source_table(db_session, source)

    resp_bad = await auth_client.post(
        f"/projects/{project.id}/sources/{source.id}/tables/{st.id}/columns",
        json={
            "name": "calc_col",
            "type": "metric",
            "data_type": "float",
            "description": "Расчетная",
            "is_calculated": True,
            "formula": None,
        },
    )
    assert resp_bad.status_code == 422
    assert "formula обязательна" in str(resp_bad.json()["detail"])

    resp_ok = await auth_client.post(
        f"/projects/{project.id}/sources/{source.id}/tables/{st.id}/columns",
        json={
            "name": "calc_col",
            "type": "metric",
            "data_type": "float",
            "description": "Расчетная",
            "is_calculated": True,
            "formula": "revenue / 1000",
        },
    )
    assert resp_ok.status_code == 201
