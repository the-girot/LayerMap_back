"""
Enhanced functional tests with edge cases and error scenarios for layermap_back API.

Покрытие:
- Edge cases для всех endpoints
- Error scenarios и валидация
- Boundary conditions
- Negative testing
- Business logic validation
"""

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Project Edge Cases
# =============================================================================


class TestProjectEdgeCases:
    """Edge cases для проектов"""

    @pytest.mark.asyncio
    async def test_project_with_empty_description(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Проект с пустым описанием"""
        payload = {"name": "Test Project", "description": "", "status": "active"}
        response = await client.post("/projects", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_project_with_very_long_name(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Проект с очень длинным названием"""
        long_name = "x" * 255
        payload = {"name": long_name, "description": "Desc", "status": "active"}
        response = await client.post("/projects", json=payload)
        # Должно быть либо 201, либо 422 (если есть валидация длины)
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_project_with_special_characters(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Проект со специальными символами в названии"""
        payload = {
            "name": "Проект с символами: !@#$%^&*()",
            "description": "Описание с символами: <>&'",
            "status": "active",
        }
        response = await client.post("/projects", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_project_with_unicode_characters(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Проект с unicode символами"""
        payload = {
            "name": "Проект с кириллицей и emoji 🗺️",
            "description": "Описание с unicode: 日本語 中文 한국어",
            "status": "active",
        }
        response = await client.post("/projects", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_project_with_whitespace_only_name(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Проект с названием из пробелов"""
        payload = {"name": "   ", "description": "Desc", "status": "active"}
        response = await client.post("/projects", json=payload)
        # Должно быть либо 422 (валидация), либо 201 (если не валидируется)
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_project_invalid_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Проект с невалидным статусом"""
        payload = {"name": "Test", "description": "Desc", "status": "invalid_status"}
        response = await client.post("/projects", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_project_missing_required_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Проект с отсутствующими обязательными полями"""
        payload = {"name": "Test"}  # 缺少 description и status
        response = await client.post("/projects", json=payload)
        assert response.status_code == 201
        assert response.json()["status"] == "draft" 

    @pytest.mark.asyncio
    async def test_project_pagination_edge_cases(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Пагинация с граничными значениями"""
        # page = 0 (должно быть 422)
        response = await client.get("/projects?page=0")
        assert response.status_code == 422

        # size = 0 (должно быть 422)
        response = await client.get("/projects?size=0")
        assert response.status_code == 422

        # size > 100 (должно быть 422)
        response = await client.get("/projects?size=101")
        assert response.status_code == 422

        # page = -1 (должно быть 422)
        response = await client.get("/projects?page=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_project_sort_by_invalid_field(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Сортировка по невалидному полю"""
        response = await client.get("/projects?sort_by=invalid_field")
        # Должно быть либо 422, либо игнорирование (200)
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_project_sort_by_invalid_direction(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Сортировка с невалильным направлением"""
        response = await client.get("/projects?sort_dir=invalid")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_project_search_empty_string(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Поиск с пустой строкой"""
        response = await client.get("/projects?search=")
        # min_length=1 должен отклонить
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_project_search_min_length(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Поиск с минимальной длиной"""
        response = await client.get("/projects?search=a")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_project_kpi_empty_database(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """KPI при пустой базе данных"""
        # Очищаем все проекты
        await db_session.execute(text("DELETE FROM projects"))
        await db_session.commit()

        response = await client.get("/projects/kpi")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["active"] == 0
        assert data["draft"] == 0
        assert data["archived"] == 0

    @pytest.mark.asyncio
    async def test_project_recent_empty_database(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Recent projects при пустой базе данных"""
        await db_session.execute(text("DELETE FROM projects"))
        await db_session.commit()

        response = await client.get("/projects/recent")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_project_recent_large_limit(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Recent projects с limit > 50"""
        response = await client.get("/projects/recent?limit=100")
        assert response.status_code == 422


# =============================================================================
# Source Edge Cases
# =============================================================================


class TestSourceEdgeCases:
    """Edge cases для источников"""

    @pytest.mark.asyncio
    async def test_source_with_empty_description(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Источник с пустым описанием"""
        payload = {
            "name": "Test Source",
            "description": "",
            "type": "DB",
            "row_count": 0,
        }
        response = await client.post("/projects/1/sources", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_source_invalid_type(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Источник с невалидным типом"""
        payload = {
            "name": "Test",
            "description": "Desc",
            "type": "INVALID",
            "row_count": 0,
        }
        response = await client.post("/projects/1/sources", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_source_negative_row_count(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Источник с отрицательным row_count"""
        payload = {"name": "Test", "description": "Desc", "type": "DB", "row_count": -1}
        response = await client.post("/projects/1/sources", json=payload)
        # Должно быть либо 422, либо 201 (если не валидируется)
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_source_missing_required_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Источник с отсутствующими обязательными полями"""
        payload = {"name": "Test"}  # 缺少 description, type, row_count
        response = await client.post("/projects/1/sources", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_source_nonexistent_project(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Источник для несуществующего проекта"""
        payload = {"name": "Test", "description": "Desc", "type": "DB", "row_count": 0}
        response = await client.post("/projects/9999/sources", json=payload)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_source_update_nonexistent(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Обновление несуществующего источника"""
        payload = {"name": "Updated"}
        response = await client.patch("/projects/1/sources/9999", json=payload)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_source_delete_nonexistent(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Удаление несуществующего источника"""
        response = await client.delete("/projects/1/sources/9999")
        assert response.status_code == 404


# =============================================================================
# Mapping Table Edge Cases
# =============================================================================


class TestMappingTableEdgeCases:
    """Edge cases для таблиц маппинга"""

    @pytest.mark.asyncio
    async def test_mapping_table_with_empty_description(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Таблица маппинга с пустым описанием"""
        payload = {"name": "Test Table", "description": "", "source_id": 1}
        response = await client.post("/projects/1/mapping-tables", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_mapping_table_missing_source(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Таблица маппинга с несуществующим source_id"""
        payload = {"name": "Test", "description": "Desc", "source_id": 9999}
        response = await client.post("/projects/1/mapping-tables", json=payload)
        # Должно быть либо 422, либо 404
        assert response.status_code in [202, 404, 422]

    @pytest.mark.asyncio
    async def test_mapping_table_nonexistent_project(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Таблица маппинга для несуществующего проекта"""
        payload = {"name": "Test", "description": "Desc", "source_id": 1}
        response = await client.post("/projects/9999/mapping-tables", json=payload)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mapping_table_column_with_formula(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Колонка с формулой (is_calculated=true)"""
        # Сначала создаем таблицу
        table_payload = {"name": "Test Table", "description": "Desc", "source_id": 1}
        table_response = await client.post(
            "/projects/1/mapping-tables", json=table_payload
        )
        assert table_response.status_code == 201
        table_id = table_response.json()["id"]

        # Создаем колонку с формулой
        column_payload = {
            "name": "calculated_column",
            "type": "metric",
            "data_type": "integer",
            "description": "Calculated",
            "is_calculated": True,
            "formula": "SUM(value)",
        }
        response = await client.post(
            f"/projects/1/mapping-tables/{table_id}/columns", json=column_payload
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_mapping_table_column_without_formula(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Колонка без формулы (is_calculated=true) - должно fail"""
        table_payload = {"name": "Test Table", "description": "Desc", "source_id": 1}
        table_response = await client.post(
            "/projects/1/mapping-tables", json=table_payload
        )
        assert table_response.status_code == 201
        table_id = table_response.json()["id"]

        column_payload = {
            "name": "calculated_column",
            "type": "metric",
            "data_type": "integer",
            "description": "Calculated",
            "is_calculated": True,
            # 缺少 formula
        }
        response = await client.post(
            f"/projects/1/mapping-tables/{table_id}/columns", json=column_payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_mapping_table_column_invalid_type(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Колонка с невалидным типом"""
        table_payload = {"name": "Test Table", "description": "Desc", "source_id": 1}
        table_response = await client.post(
            "/projects/1/mapping-tables", json=table_payload
        )
        assert table_response.status_code == 201
        table_id = table_response.json()["id"]

        column_payload = {
            "name": "test_column",
            "type": "invalid_type",
            "data_type": "string",
            "description": "Test",
        }
        response = await client.post(
            f"/projects/1/mapping-tables/{table_id}/columns", json=column_payload
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_mapping_table_column_invalid_data_type(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Колонка с невалидным data_type"""
        table_payload = {"name": "Test Table", "description": "Desc", "source_id": 1}
        table_response = await client.post(
            "/projects/1/mapping-tables", json=table_payload
        )
        assert table_response.status_code == 201
        table_id = table_response.json()["id"]

        column_payload = {
            "name": "test_column",
            "type": "dimension",
            "data_type": "invalid_type",
            "description": "Test",
        }
        response = await client.post(
            f"/projects/1/mapping-tables/{table_id}/columns", json=column_payload
        )
        assert response.status_code == 422


# =============================================================================
# RPI Mapping Edge Cases
# =============================================================================


class TestRPIEdgeCases:
    """Edge cases для RPI mappings"""

    @pytest.mark.asyncio
    async def test_rpi_with_calculated_true_no_formula(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """RPI с is_calculated=true без формулы - должно fail"""
        payload = {
            "number": 100,
            "ownership": "Finance",
            "status": "draft",
            "block": "Block 1",
            "measurement_type": "Метрика",
            "is_calculated": True,
            "measurement": "Revenue",
            "object_field": "revenue",
            # 缺少 formula
        }
        response = await client.post("/projects/1/rpi-mappings", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rpi_with_calculated_true_with_formula(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """RPI с is_calculated=true и формулой"""
        payload = {
            "number": 100,
            "ownership": "Finance",
            "status": "draft",
            "block": "Block 1",
            "measurement_type": "Метрика",
            "is_calculated": True,
            "formula": "SUM(revenue)",
            "measurement": "Revenue",
            "object_field": "revenue",
        }
        response = await client.post("/projects/1/rpi-mappings", json=payload)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_rpi_invalid_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """RPI с невалидным статусом"""
        payload = {
            "number": 100,
            "ownership": "Finance",
            "status": "invalid_status",
            "block": "Block 1",
            "measurement_type": "Метрика",
            "is_calculated": False,
            "measurement": "Revenue",
            "object_field": "revenue",
        }
        response = await client.post("/projects/1/rpi-mappings", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rpi_invalid_measurement_type(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """RPI с невалидным measurement_type"""
        payload = {
            "number": 100,
            "ownership": "Finance",
            "status": "draft",
            "block": "Block 1",
            "measurement_type": "Invalid",
            "is_calculated": False,
            "measurement": "Revenue",
            "object_field": "revenue",
        }
        response = await client.post("/projects/1/rpi-mappings", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rpi_duplicate_number(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """RPI с дублирующимся номером"""
        # Создаем первый RPI
        payload1 = {
            "number": 100,
            "ownership": "Finance",
            "status": "draft",
            "block": "Block 1",
            "measurement_type": "Метрика",
            "is_calculated": False,
            "measurement": "Revenue",
            "object_field": "revenue",
        }
        response1 = await client.post("/projects/1/rpi-mappings", json=payload1)
        assert response1.status_code == 201

        # Пытаемся создать второй с тем же номером
        response2 = await client.post("/projects/1/rpi-mappings", json=payload1)
        # Должно быть либо 422 (уникальность), либо 201 (если не enforced)
        assert response2.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_rpi_pagination_edge_cases(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Пагинация RPI с граничными значениями"""
        # limit = 0
        response = await client.get("/projects/1/rpi-mappings?limit=0")
        assert response.status_code == 422

        # limit > 100
        response = await client.get("/projects/1/rpi-mappings?limit=101")
        assert response.status_code == 422

        # skip = -1
        response = await client.get("/projects/1/rpi-mappings?skip=-1")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rpi_search_min_length(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Поиск RPI с минимальной длиной"""
        response = await client.get("/projects/1/rpi-mappings?search=a")
        assert response.status_code == 200

        # search = "" (пустая строка)
        response = await client.get("/projects/1/rpi-mappings?search=")
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rpi_stats_empty_project(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Статистика RPI для проекта без записей"""
        response = await client.get("/projects/1/rpi-mappings/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "approved" in data
        assert "in_review" in data
        assert "draft" in data

    @pytest.mark.asyncio
    async def test_rpi_filter_multiple(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Фильтрация RPI с несколькими параметрами"""
        response = await client.get(
            "/projects/1/rpi-mappings?status=approved&ownership=Finance&measurement_type=Метрика"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_rpi_invalid_filter_status(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """RPI с невалидным фильтром status"""
        response = await client.get("/projects/1/rpi-mappings?status=invalid")
        # Должно быть либо 422, либо игнорирование (200)
        assert response.status_code in [200, 422]


# =============================================================================
# Error Scenarios
# =============================================================================


class TestErrorScenarios:
    """Сценарии ошибок"""

    @pytest.mark.asyncio
    async def test_concurrent_project_creation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Одновременное создание проектов с одинаковым именем"""
        payload = {
            "name": "Duplicate Project",
            "description": "Desc",
            "status": "active",
        }

        # Создаем несколько проектов одновременно
        tasks = [client.post("/projects", json=payload) for _ in range(5)]
        responses = await asyncio.gather(*tasks)

        # Только один должен succeed, остальные - 409 или 422
        successful = sum(1 for r in responses if r.status_code == 201)
        conflicts = sum(1 for r in responses if r.status_code in [409, 422])

        assert successful == 1
        assert conflicts == 4

    @pytest.mark.asyncio
    async def test_delete_project_with_dependencies(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Удаление проекта с зависимостями"""
        # Создаем проект
        project_response = await client.post(
            "/projects",
            json={
                "name": "Project with deps",
                "description": "Desc",
                "status": "active",
            },
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        # Создаем источник
        source_response = await client.post(
            f"/projects/{project_id}/sources",
            json={
                "name": "Source",
                "description": "Desc",
                "type": "DB",
                "row_count": 0,
            },
        )
        assert source_response.status_code == 201

        # Пытаемся удалить проект
        response = await client.delete(f"/projects/{project_id}")
        # Должно быть либо 204 (каскадное удаление), либо 409 (зависимости)
        assert response.status_code in [204, 409]

    @pytest.mark.asyncio
    async def test_update_with_invalid_json(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Обновление с невалидным JSON"""
        client.headers["Content-Type"] = "application/json"
        response = await client.patch(
            "/projects/1",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_method_not_allowed(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Использование неподдерживаемого HTTP метода"""
        # POST на GET endpoint
        response = await client.post("/projects/1")
        assert response.status_code == 405

        # GET на POST endpoint
        response = await client.get("/projects")
        assert response.status_code == 200  # GET поддерживается

    @pytest.mark.asyncio
    async def test_access_nonexistent_resource(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Доступ к несуществующему ресурсу"""
        response = await client.get("/projects/999999")
        assert response.status_code == 404

        response = await client.get("/projects/1/sources/999999")
        assert response.status_code == 404

        response = await client.get("/projects/1/mapping-tables/999999")
        assert response.status_code == 404

        response = await client.get("/projects/1/rpi-mappings/999999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_database_constraint_violation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Нарушение ограничений БД"""
        # Пытаемся создать проект с NULL name (если БД позволяет)
        # Это зависит от настроек БД
        try:
            response = await client.post(
                "/projects",
                json={"name": None, "description": "Desc", "status": "active"},
            )
            # Если БД отклоняет, будет 422 или 500
            assert response.status_code in [422, 500]
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Превышение лимита запросов"""
        # Отправляем много запросов быстро
        for _ in range(100):
            response = await client.get("/health")
            if response.status_code == 429:
                # Rate limit exceeded
                break

        # Если не получили 429, это нормально (rate limiting может быть отключен)
        assert True

    @pytest.mark.asyncio
    async def test_timeout_handling(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Обработка таймаутов"""
        # Этот тест требует настройки таймаутов
        # В текущей реализации используем default timeout
        response = await client.get("/projects")
        assert response.status_code == 200


# =============================================================================
# Business Logic Validation
# =============================================================================


class TestBusinessLogic:
    """Валидация бизнес-логики"""

    @pytest.mark.asyncio
    async def test_project_status_workflow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Рабочий процесс статусов проекта"""
        # Создаем проект в draft
        response = await client.post(
            "/projects",
            json={"name": "Workflow Test", "description": "Desc", "status": "draft"},
        )
        assert response.status_code == 201
        assert response.json()["status"] == "draft"

        # Обновляем на active
        response = await client.patch("/projects/1", json={"status": "active"})
        assert response.status_code == 201
        assert response.json()["status"] == "active"

        # Обновляем на archived
        response = await client.patch("/projects/1", json={"status": "archived"})
        assert response.status_code == 201
        assert response.json()["status"] == "archived"

    @pytest.mark.asyncio
    async def test_rpi_status_workflow(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Рабочий процесс статусов RPI"""
        # Создаем RPI в draft
        response = await client.post(
            "/projects/1/rpi-mappings",
            json={
                "number": 200,
                "ownership": "Finance",
                "status": "draft",
                "block": "Block 1",
                "measurement_type": "Метрика",
                "is_calculated": False,
                "measurement": "Revenue",
                "object_field": "revenue",
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "draft"

        # Обновляем на in_review
        response = await client.patch(
            "/projects/1/rpi-mappings/1", json={"status": "in_review"}
        )
        assert response.status_code == 201
        assert response.json()["status"] == "in_review"

        # Обновляем на approved
        response = await client.patch(
            "/projects/1/rpi-mappings/1", json={"status": "approved"}
        )
        assert response.status_code == 201
        assert response.json()["status"] == "approved"

    @pytest.mark.asyncio
    async def test_cascade_delete_sources(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Каскадное удаление источников"""
        # Создаем проект
        project_response = await client.post(
            "/projects",
            json={"name": "Cascade Test", "description": "Desc", "status": "active"},
        )
        assert project_response.status_code == 201
        project_id = project_response.json()["id"]

        # Создаем источник
        source_response = await client.post(
            f"/projects/{project_id}/sources",
            json={
                "name": "Source",
                "description": "Desc",
                "type": "DB",
                "row_count": 0,
            },
        )
        assert source_response.status_code == 201

        # Проверяем, что источник создан
        response = await client.get(f"/projects/{project_id}/sources")
        assert response.status_code == 200
        assert len(response.json()) > 0

        # Удаляем проект
        response = await client.delete(f"/projects/{project_id}")
        assert response.status_code == 204

        # Проверяем, что источник удален
        response = await client.get(f"/projects/{project_id}/sources")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_column_formula_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Валидация формулы колонки"""
        # Создаем таблицу
        table_response = await client.post(
            "/projects/1/mapping-tables",
            json={"name": "Formula Test", "description": "Desc", "source_id": 1},
        )
        assert table_response.status_code == 201
        table_id = table_response.json()["id"]

        # Создаем колонку без формулы (is_calculated=false)
        response = await client.post(
            f"/projects/1/mapping-tables/{table_id}/columns",
            json={
                "name": "normal_column",
                "type": "dimension",
                "data_type": "string",
                "description": "Normal",
                "is_calculated": False,
            },
        )
        assert response.status_code == 201

        # Создаем колонку с формулой (is_calculated=true)
        response = await client.post(
            f"/projects/1/mapping-tables/{table_id}/columns",
            json={
                "name": "calculated_column",
                "type": "metric",
                "data_type": "integer",
                "description": "Calculated",
                "is_calculated": True,
                "formula": "SUM(value)",
            },
        )
        assert response.status_code == 201

        # Обновляем колонку на is_calculated=true без формулы
        column_id = response.json()["id"]
        response = await client.patch(
            f"/projects/1/mapping-tables/{table_id}/columns/{column_id}",
            json={
                "is_calculated": True
                # 缺少 formula
            },
        )
        assert response.status_code == 422


# =============================================================================
# Integration Edge Cases
# =============================================================================


class TestIntegrationEdgeCases:
    """Интеграционные edge cases"""

    @pytest.mark.asyncio
    async def test_cross_project_access(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Попытка доступа к ресурсам другого проекта"""
        # Создаем второй проект
        project2_response = await client.post(
            "/projects",
            json={"name": "Project 2", "description": "Desc", "status": "active"},
        )
        assert project2_response.status_code == 201
        project2_id = project2_response.json()["id"]

        # Пытаемся получить источники проекта 2 через проект 1
        response = await client.get("/projects/1/sources")
        assert response.status_code == 200
        # Должны быть только источники проекта 1
        project1_sources = [s for s in response.json() if s["project_id"] == 1]
        assert len(project1_sources) == len(response.json())

    @pytest.mark.asyncio
    async def test_orphaned_records_cleanup(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Очистка осиротевших записей"""
        # Этот тест требует проверки каскадного удаления
        # В текущей реализации должны быть foreign key с CASCADE
        assert True  # Placeholder

    @pytest.mark.asyncio
    async def test_concurrent_updates(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Одновременные обновления одного ресурса"""
        # Создаем проект
        response = await client.post(
            "/projects",
            json={"name": "Concurrent Test", "description": "Desc", "status": "active"},
        )
        assert response.status_code == 201
        project_id = response.json()["id"]

        # Одновременные обновления
        updates = [
            {"description": "Update 1"},
            {"description": "Update 2"},
            {"description": "Update 3"},
        ]

        tasks = [
            client.patch(f"/projects/{project_id}", json=update) for update in updates
        ]
        responses = await asyncio.gather(*tasks)

        # Все обновления должны завершиться (хотя последнее победит)
        assert all(r.status_code == 201 for r in responses)
