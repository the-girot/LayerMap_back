import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    create_mapping_column,
    create_mapping_table,
    create_project,
    create_source,
)


@pytest.mark.anyio
async def test_create_mapping_table(auth_client: AsyncClient, db_session: AsyncSession):
    project = await create_project(db_session)
    source = await create_source(db_session, project)

    resp = await auth_client.post(
        f"/projects/{project.id}/mapping-tables",
        json={
            "name": "Таблица клиентов",
            "description": "Описание",
            "source_id": source.id,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == project.id
    assert data["source_id"] == source.id


@pytest.mark.anyio
async def test_list_mapping_tables_with_columns(
    auth_client: AsyncClient, db_session: AsyncSession
):
    project = await create_project(db_session)
    mt = await create_mapping_table(db_session, project)
    await create_mapping_column(db_session, mt, name="customer_id")

    resp = await auth_client.get(f"/projects/{project.id}/mapping-tables")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["columns"][0]["name"] == "customer_id"


@pytest.mark.anyio
async def test_create_mapping_column_requires_formula_if_calculated(
    auth_client: AsyncClient, db_session: AsyncSession
):
    project = await create_project(db_session)
    mt = await create_mapping_table(db_session, project)

    resp_bad = await auth_client.post(
        f"/projects/{project.id}/mapping-tables/{mt.id}/columns",
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
        f"/projects/{project.id}/mapping-tables/{mt.id}/columns",
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
