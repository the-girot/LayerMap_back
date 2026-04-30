"""
Тесты DWH API: CRUD для DWHTable, DWHColumn, LayerMapping + /lineage.

Следуют стилю существующих тестов проекта (test_source_tables_api.py и др.).
"""

import pytest

from tests.factories import (
    create_dwh_column,
    create_dwh_table,
    create_layer_mapping,
    create_project,
)


# ══════════════════════════════════════════════════════════════════════
# DWHTable CRUD
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_dwh_table(auth_client, db_session):
    """Создание DWH-таблицы."""
    project = await create_project(db_session)

    resp = await auth_client.post(
        f"/projects/{project.id}/dwh-tables",
        json={"name": "stg_orders", "layer": "STG", "description": "Staging orders"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "stg_orders"
    assert data["layer"] == "STG"
    assert data["project_id"] == project.id


@pytest.mark.asyncio
async def test_list_dwh_tables(auth_client, db_session):
    """Список DWH-таблиц проекта."""
    project = await create_project(db_session)
    await create_dwh_table(db_session, project, "STG", "stg_orders")
    await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.get(f"/projects/{project.id}/dwh-tables")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_dwh_table(auth_client, db_session):
    """Получение одной DWH-таблицы."""
    project = await create_project(db_session)
    table = await create_dwh_table(db_session, project, "STG", "stg_orders")
    await create_dwh_column(db_session, table, "id", "integer")

    resp = await auth_client.get(
        f"/projects/{project.id}/dwh-tables/{table.id}"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "stg_orders"
    assert len(data["columns"]) == 1


@pytest.mark.asyncio
async def test_update_dwh_table(auth_client, db_session):
    """Обновление DWH-таблицы."""
    project = await create_project(db_session)
    table = await create_dwh_table(db_session, project, "STG", "stg_orders")

    resp = await auth_client.patch(
        f"/projects/{project.id}/dwh-tables/{table.id}",
        json={"description": "Updated description"},
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_dwh_table(auth_client, db_session):
    """Удаление DWH-таблицы."""
    project = await create_project(db_session)
    table = await create_dwh_table(db_session, project, "STG", "stg_orders")

    resp = await auth_client.delete(
        f"/projects/{project.id}/dwh-tables/{table.id}"
    )
    assert resp.status_code == 204

    # Проверяем, что таблица удалена
    resp = await auth_client.get(
        f"/projects/{project.id}/dwh-tables/{table.id}"
    )
    assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# DWHColumn CRUD
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_dwh_column(auth_client, db_session):
    """Создание колонки в DWH-таблице."""
    project = await create_project(db_session)
    table = await create_dwh_table(db_session, project, "STG", "stg_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/dwh-tables/{table.id}/columns",
        json={
            "name": "order_id",
            "data_type": "integer",
            "description": "ID заказа",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "order_id"
    assert data["dwh_table_id"] == table.id


@pytest.mark.asyncio
async def test_list_dwh_columns(auth_client, db_session):
    """Список колонок DWH-таблицы."""
    project = await create_project(db_session)
    table = await create_dwh_table(db_session, project, "STG", "stg_orders")
    await create_dwh_column(db_session, table, "col_1")
    await create_dwh_column(db_session, table, "col_2")

    resp = await auth_client.get(
        f"/projects/{project.id}/dwh-tables/{table.id}/columns"
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_delete_dwh_column_cascade(auth_client, db_session):
    """Удаление таблицы каскадно удаляет колонки."""
    project = await create_project(db_session)
    table = await create_dwh_table(db_session, project, "STG", "stg_orders")
    await create_dwh_column(db_session, table, "col_1")

    await auth_client.delete(f"/projects/{project.id}/dwh-tables/{table.id}")

    resp = await auth_client.get(
        f"/projects/{project.id}/dwh-tables/{table.id}/columns"
    )
    assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# LayerMapping CRUD
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_create_layer_mapping(auth_client, db_session):
    """Создание маппинга ODS из одной STG."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")

    resp = await auth_client.post(
        f"/projects/{project.id}/layer-mappings",
        json={
            "targetTableId": ods.id,
            "sourceTableIds": [stg.id],
            "transformation": "SELECT * FROM stg_orders",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["target_table_id"] == ods.id
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source_table_id"] == stg.id


@pytest.mark.asyncio
async def test_list_layer_mappings(auth_client, db_session):
    """Список маппингов проекта."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    await create_layer_mapping(db_session, project, ods, [stg])

    resp = await auth_client.get(
        f"/projects/{project.id}/layer-mappings"
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_update_layer_mapping(auth_client, db_session):
    """Обновление маппинга (transformation/algorithm)."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    mapping = await create_layer_mapping(db_session, project, ods, [stg])

    resp = await auth_client.patch(
        f"/projects/{project.id}/layer-mappings/{mapping.id}",
        json={"transformation": "UPDATED", "algorithm": "new_algo"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["transformation"] == "UPDATED"
    assert data["algorithm"] == "new_algo"


@pytest.mark.asyncio
async def test_delete_layer_mapping(auth_client, db_session):
    """Удаление маппинга."""
    project = await create_project(db_session)
    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    mapping = await create_layer_mapping(db_session, project, ods, [stg])

    resp = await auth_client.delete(
        f"/projects/{project.id}/layer-mappings/{mapping.id}"
    )
    assert resp.status_code == 204

    resp = await auth_client.get(
        f"/projects/{project.id}/layer-mappings/{mapping.id}"
    )
    assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════
# Lineage
# ══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_lineage(auth_client, db_session):
    """Получение графа lineage проекта."""
    project = await create_project(db_session)

    stg = await create_dwh_table(db_session, project, "STG", "stg_orders")
    await create_dwh_column(db_session, stg, "order_id", "integer")

    ods = await create_dwh_table(db_session, project, "ODS", "ods_orders")
    await create_dwh_column(db_session, ods, "order_id", "integer")

    await create_layer_mapping(
        db_session, project, ods, [stg],
        transformation="SELECT * FROM stg_orders",
    )

    resp = await auth_client.get(f"/projects/{project.id}/lineage")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tables"]) == 2
    assert len(data["mappings"]) == 1
    assert data["mappings"][0]["target_table_id"] == ods.id
    assert data["mappings"][0]["source_table_ids"] == [stg.id]

    # Проверяем, что колонки тоже пришли
    for t in data["tables"]:
        if t["id"] == stg.id:
            assert len(t["columns"]) == 1
            assert t["columns"][0]["name"] == "order_id"


@pytest.mark.asyncio
async def test_lineage_empty_project(auth_client, db_session):
    """Lineage пустого проекта."""
    project = await create_project(db_session)
    resp = await auth_client.get(f"/projects/{project.id}/lineage")
    assert resp.status_code == 200
    assert resp.json() == {"tables": [], "mappings": []}
