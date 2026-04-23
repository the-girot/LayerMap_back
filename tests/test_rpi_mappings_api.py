import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import (
    create_mapping_column,
    create_mapping_table,
    create_project,
    create_rpi,
)


@pytest.mark.anyio
async def test_create_rpi_requires_formula_if_calculated(
    auth_client: AsyncClient, db_session: AsyncSession
):
    project = await create_project(db_session)
    mt = await create_mapping_table(db_session, project)
    col = await create_mapping_column(db_session, mt)

    resp_bad = await auth_client.post(
        f"/projects/{project.id}/rpi-mappings",
        json={
            "number": 42,
            "ownership": "Финансовый департамент",
            "status": "draft",
            "block": "Блок 1",
            "measurement_type": "metric",
            "is_calculated": True,
            "formula": None,
            "measurement": "Выручка",
            "measurement_description": "Общая выручка",
            "source_report": "Отчёт 123",
            "object_field": "revenue",
            "source_column_id": col.id,
            "date_added": "2024-01-01",
            "date_removed": None,
            "comment": "В работе",
            "verification_file": None,
        },
    )
    assert resp_bad.status_code in (400, 422)

    resp_ok = await auth_client.post(
        f"/projects/{project.id}/rpi-mappings",
        json={
            "number": 43,
            "ownership": "Финансовый департамент",
            "status": "draft",
            "block": "Блок 1",
            "measurement_type": "metric",
            "is_calculated": False,
            "formula": None,
            "measurement": "Выручка",
            "measurement_description": "Общая выручка",
            "source_report": "Отчёт 123",
            "object_field": "revenue",
            "source_column_id": col.id,
            "date_added": "2024-01-01",
            "date_removed": None,
            "comment": "В работе",
            "verification_file": None,
        },
    )
    assert resp_ok.status_code == 201


@pytest.mark.anyio
async def test_rpi_list_filters_and_pagination(
    auth_client: AsyncClient, db_session: AsyncSession
):
    project = await create_project(db_session)
    mt = await create_mapping_table(db_session, project)
    col = await create_mapping_column(db_session, mt)
    await create_rpi(db_session, project, col)
    await create_rpi(db_session, project, col)
    await create_rpi(db_session, project, col)

    resp = await auth_client.get(
        f"/projects/{project.id}/rpi-mappings",
        params={"skip": 0, "limit": 2},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

    resp2 = await auth_client.get(
        f"/projects/{project.id}/rpi-mappings",
        params={"status": "draft"},
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) >= 1


@pytest.mark.anyio
async def test_rpi_stats(auth_client: AsyncClient, db_session: AsyncSession):
    project = await create_project(db_session)
    mt = await create_mapping_table(db_session, project)
    col = await create_mapping_column(db_session, mt)
    await create_rpi(db_session, project, col)

    resp = await auth_client.get(f"/projects/{project.id}/rpi-mappings/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] >= 1
    assert data["draft"] >= 1
