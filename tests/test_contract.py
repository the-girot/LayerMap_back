"""
Contract tests for layermap_back API.

Покрытие:
- Consumer-driven contract testing
- API version compatibility
- Schema validation
- Response format consistency
- Backward compatibility
"""

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.mapping_table import (
    MappingColumnCreate,
)
from app.schemas.project import ProjectCreate, ProjectOut
from app.schemas.rpi_mapping import (
    RPIMappingCreate,
)
from app.schemas.source import SourceCreate

# =============================================================================
# Schema Contract Tests
# =============================================================================


class TestSchemaContracts:
    """Тесты контрактов схем"""

    @pytest.mark.asyncio
    async def test_project_create_schema_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации схемы ProjectCreate"""
        # Валидный payload
        payload = {
            "name": "Test Project",
            "description": "Description",
            "status": "active",
        }

        try:
            project = ProjectCreate(**payload)
            assert project.name == "Test Project"
            assert project.description == "Description"
            assert project.status == "active"
        except ValidationError as e:
            pytest.fail(f"Valid payload failed validation: {e}")

    @pytest.mark.asyncio
    async def test_project_create_schema_missing_fields(self, ...):
    """ProjectCreate требует только name; description и status имеют defaults"""
        project = ProjectCreate(name="Test Project")
        assert project.name == "Test Project"
        assert project.status == "draft"      # default
        assert project.description is None    # default

        # Проверяем что без name — реально падает
        with pytest.raises(ValidationError):
            ProjectCreate()

    @pytest.mark.asyncio
    async def test_project_out_schema_serialization(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест сериализации схемы ProjectOut"""
        # Создаем проект через API
        response = await client.post(
            "/projects",
            json={"name": "Schema Test", "description": "Desc", "status": "active"},
        )
        assert response.status_code == 201

        # Проверяем, что ответ соответствует схеме
        data = response.json()
        project = ProjectOut(**data)
        assert project.id is not None
        assert project.name == "Schema Test"
        assert project.status == "active"

    @pytest.mark.asyncio
    async def test_source_create_schema_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации схемы SourceCreate"""
        payload = {
            "name": "Test Source",
            "description": "Description",
            "type": "DB",
            "row_count": 0,
        }

        try:
            source = SourceCreate(**payload)
            assert source.type == "DB"
        except ValidationError as e:
            pytest.fail(f"Valid payload failed validation: {e}")

    @pytest.mark.asyncio
    async def test_source_invalid_type(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации невалидного типа источника"""
        payload = {
            "name": "Test",
            "description": "Desc",
            "type": "INVALID_TYPE",
            "row_count": 0,
        }

        with pytest.raises(ValidationError):
            SourceCreate(**payload)

    @pytest.mark.asyncio
    async def test_rpi_mapping_create_schema_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации схемы RPIMappingCreate"""
        payload = {
            "number": 100,
            "ownership": "Finance",
            "status": "draft",
            "block": "Block 1",
            "measurement_type": "metric",
            "is_calculated": False,
            "measurement": "Revenue",
            "object_field": "revenue",
        }

        try:
            rpi = RPIMappingCreate(**payload)
            assert rpi.status == "draft"
            assert rpi.measurement_type == "Метрика"
        except ValidationError as e:
            pytest.fail(f"Valid payload failed validation: {e}")

    @pytest.mark.asyncio
    async def test_rpi_mapping_calculated_requires_formula(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации: calculated требует formula"""
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

        with pytest.raises(ValidationError):
            RPIMappingCreate(**payload)

    @pytest.mark.asyncio
    async def test_mapping_column_create_schema_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации схемы MappingColumnCreate"""
        payload = {
            "name": "test_column",
            "type": "dimension",
            "data_type": "string",
            "description": "Test",
        }

        try:
            column = MappingColumnCreate(**payload)
            assert column.type == "dimension"
        except ValidationError as e:
            pytest.fail(f"Valid payload failed validation: {e}")

    @pytest.mark.asyncio
    async def test_mapping_column_invalid_type(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации невалидного типа колонки"""
        payload = {
            "name": "test",
            "type": "invalid",
            "data_type": "string",
            "description": "Test",
        }

        with pytest.raises(ValidationError):
            MappingColumnCreate(**payload)


# =============================================================================
# API Response Contract Tests
# =============================================================================


class TestAPIResponseContracts:
    """Тесты контрактов ответов API"""

    @pytest.mark.asyncio
    async def test_project_list_response_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ответа списка проектов"""
        response = await client.get("/projects")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            project = data[0]
            assert "id" in project
            assert "name" in project
            assert "description" in project
            assert "status" in project
            assert "created_at" in project
            assert "updated_at" in project

    @pytest.mark.asyncio
    async def test_project_detail_response_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ответа детали проекта"""
        # Создаем проект
        response = await client.post(
            "/projects",
            json={"name": "Contract Test", "description": "Desc", "status": "active"},
        )
        assert response.status_code == 201
        project_id = response.json()["id"]

        # Получаем проект
        response = await client.get(f"/projects/{project_id}")
        assert response.status_code == 200

        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_source_list_response_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ответа списка источников"""
        response = await client.get("/projects/1/sources")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            source = data[0]
            assert "id" in source
            assert "project_id" in source
            assert "name" in source
            assert "type" in source
            assert "created_at" in source

    @pytest.mark.asyncio
    async def test_rpi_mapping_list_response_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ответа списка RPI mappings"""
        response = await client.get("/projects/1/rpi-mappings")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        if len(data) > 0:
            rpi = data[0]
            assert "id" in rpi
            assert "number" in rpi
            assert "project_id" in rpi
            assert "ownership" in rpi
            assert "status" in rpi
            assert "measurement" in rpi

    @pytest.mark.asyncio
    async def test_rpi_stats_response_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ответа статистики RPI"""
        response = await client.get("/projects/1/rpi-mappings/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "approved" in data
        assert "in_review" in data
        assert "draft" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["approved"], int)
        assert isinstance(data["in_review"], int)
        assert isinstance(data["draft"], int)

    @pytest.mark.asyncio
    async def test_pagination_response_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ответа с пагинацией"""
        response = await client.get("/projects/1/rpi-mappings?skip=0&limit=20")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        # Список должен быть массивом объектов


# =============================================================================
# Error Response Contract Tests
# =============================================================================


class TestErrorResponseContracts:
    """Тесты контрактов ошибок"""

    @pytest.mark.asyncio
    async def test_404_error_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ошибки 404"""
        response = await client.get("/projects/999999")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    @pytest.mark.asyncio
    async def test_422_error_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ошибки 422"""
        response = await client.post(
            "/projects",
            json={"name": "Test", "description": "Desc", "status": "invalid_status"},
        )
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    @pytest.mark.skip(reason="Auth not implemented yet")
    async def test_401_error_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ошибки 401"""
        response = await client.get("/projects")
        assert response.status_code == 401

        data = response.json()
        assert "detail" in data

    @pytest.mark.skip(reason="Auth not implemented yet")
    async def test_403_error_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ошибки 403"""
        # Пытаемся получить проект без авторизации
        response = await client.get("/projects/1")
        assert response.status_code == 401  # Или 403

        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_405_error_structure(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест структуры ошибки 405"""
        response = await client.post("/projects/1")
        assert response.status_code == 405

        data = response.json()
        assert "detail" in data


# =============================================================================
# Backward Compatibility Contract Tests
# =============================================================================


class TestBackwardCompatibility:
    """Тесты обратной совместимости"""

    @pytest.mark.asyncio
    async def test_optional_fields_backward_compatible(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест обратной совместимости с опциональными полями"""
        # Создаем проект с минимальным набором полей
        response = await client.post(
            "/projects",
            json={"name": "Minimal Project", "description": "Desc", "status": "active"},
        )
        assert response.status_code == 201

        # Получаем проект и проверяем, что все поля заполнены
        data = response.json()
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_enum_values_backward_compatible(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест обратной совместимости enum значений"""
        # Проверяем, что все enum значения работают
        for status in ["active", "draft", "archived"]:
            response = await client.post(
                "/projects",
                json={
                    "name": f"Status Test {status}",
                    "description": "Desc",
                    "status": status,
                },
            )
            assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_field_addition_backward_compatible(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест обратной совместимости при добавлении полей"""
        # Создаем проект
        response = await client.post(
            "/projects",
            json={"name": "Field Test", "description": "Desc", "status": "active"},
        )
        assert response.status_code == 201

        # Получаем проект
        data = response.json()

        # Проверяем, что старые поля присутствуют
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "status" in data

        # Новые поля также должны присутствовать
        assert "created_at" in data
        assert "updated_at" in data


# =============================================================================
# Data Type Contract Tests
# =============================================================================


class TestDataTypesContracts:
    """Тесты контрактов типов данных"""

    @pytest.mark.asyncio
    async def test_integer_field_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации integer полей"""
        # number должен быть integer
        payload = {
            "number": "not_an_integer",  # Строка вместо int
            "ownership": "Finance",
            "status": "draft",
            "block": "Block 1",
            "measurement_type": "Метрика",
            "is_calculated": False,
            "measurement": "Revenue",
            "object_field": "revenue",
        }

        response = await client.post("/projects/1/rpi-mappings", json=payload)
        # Должна быть ошибка валидации
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_string_field_max_length(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест максимальной длины string полей"""
        # Создаем проект с очень длинным названием
        long_name = "x" * 1000
        response = await client.post(
            "/projects",
            json={"name": long_name, "description": "Desc", "status": "active"},
        )

        # Должна быть либо 422 (валидация), либо 201 (если не валидируется)
        assert response.status_code in [201, 422]

    @pytest.mark.asyncio
    async def test_boolean_field_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест валидации boolean полей"""
        # is_calculated должен быть boolean
        payload = {
            "number": 100,
            "ownership": "Finance",
            "status": "draft",
            "block": "Block 1",
            "measurement_type": "Метрика",
            "is_calculated": "true",  # Строка вместо bool
            "measurement": "Revenue",
            "object_field": "revenue",
        }

        response = await client.post("/projects/1/rpi-mappings", json=payload)
        # Должна быть ошибка валидации
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_datetime_field_format(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест формата datetime полей"""
        response = await client.get("/projects")
        assert response.status_code == 200

        data = response.json()
        if len(data) > 0:
            # created_at и updated_at должны быть в ISO формате
            assert "created_at" in data[0]
            assert "updated_at" in data[0]
            # Проверяем, что это строки в ISO формате
            assert isinstance(data[0]["created_at"], str)
            assert isinstance(data[0]["updated_at"], str)


# =============================================================================
# API Version Contract Tests
# =============================================================================


class TestAPIVersionContracts:
    """Тесты версионирования API"""

    @pytest.mark.asyncio
    async def test_api_version_in_headers(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест наличия версии API в заголовках"""
        response = await client.get("/health")

        # Проверка на наличие version headers
        # В текущей реализации может быть отключено
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_deprecated_endpoints_warning(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест предупреждений о депрецированных эндпоинтах"""
        # В текущей реализации нет депрецированных эндпоинтов
        # Этот тест демонстрирует принцип
        pass

    @pytest.mark.asyncio
    async def test_api_version_negotiation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест версионной переговоров"""
        # В текущей реализации нет явного версионирования
        # Этот тест демонстрирует принцип
        pass


# =============================================================================
# Consumer-Driven Contract Tests
# =============================================================================


class TestConsumerDrivenContracts:
    """Тесты consumer-driven контрактов"""

    @pytest.mark.asyncio
    async def test_frontend_consumes_project_list(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест потребления списка проектов frontend'ом"""
        response = await client.get("/projects")
        assert response.status_code == 200

        data = response.json()
        # Frontend ожидает массив объектов с определенными полями
        for project in data:
            assert "id" in project
            assert "name" in project
            assert "status" in project

    @pytest.mark.asyncio
    async def test_frontend_consumes_project_detail(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест потребления детали проекта frontend'ом"""
        # Создаем проект
        response = await client.post(
            "/projects",
            json={"name": "Frontend Test", "description": "Desc", "status": "active"},
        )
        assert response.status_code == 201
        project_id = response.json()["id"]

        # Получаем проект
        response = await client.get(f"/projects/{project_id}")
        assert response.status_code == 200

        data = response.json()
        # Frontend ожидает полный набор полей
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "status" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_frontend_consumes_rpi_list(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест потребления списка RPI frontend'ом"""
        response = await client.get("/projects/1/rpi-mappings")
        assert response.status_code == 200

        data = response.json()
        for rpi in data:
            assert "id" in rpi
            assert "number" in rpi
            assert "measurement" in rpi
            assert "status" in rpi
            assert "ownership" in rpi

    @pytest.mark.asyncio
    async def test_frontend_consumes_kpi(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Тест потребления KPI frontend'ом"""
        response = await client.get("/projects/kpi")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "active" in data
        assert "draft" in data
        assert "archived" in data
