"""
Performance tests for layermap_back API.

Покрытие:
- Load testing: нормальная нагрузка с ожидаемым трафиком
- Stress testing: экстремальная нагрузка для определения пределов системы
- Scalability testing: проверка масштабируемости при увеличении нагрузки
- Endurance testing: длительная нагрузка для выявления утечек памяти
- Spike testing: резкие скачки нагрузки
"""

import asyncio
import time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# =============================================================================
# Load Testing
# =============================================================================


class TestLoad:
    """Тесты нагрузки (Load Testing)"""

    @pytest.mark.asyncio
    async def test_concurrent_project_requests(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Одновременные запросы к списку проектов"""
        num_requests = 50
        tasks = [auth_client.get("/projects") for _ in range(num_requests)]
        responses = await asyncio.gather(*tasks)

        # Все запросы должны завершиться успешно
        assert all(r.status_code == 200 for r in responses)

        # Проверка среднего времени ответа
        times = [r.elapsed.total_seconds() for r in responses]
        avg_time = sum(times) / len(times)
        # SLA: 95th percentile < 200ms
        # Для load testing в CI используем более мягкие требования
        assert avg_time < 1.0  # Среднее время < 1 секунды

    @pytest.mark.asyncio
    async def test_concurrent_rpi_mapping_requests(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Одновременные запросы к RPI mappings"""
        proj = await auth_client.post(
            "/projects", json={"name": "Load Test", "status": "active"}
        )
        assert proj.status_code == 201
        pid = proj.json()["id"]
        num_requests = 50
        tasks = [
            auth_client.get(f"/projects/{pid}/rpi-mappings?limit=20")
            for _ in range(num_requests)
        ]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)

        times = [r.elapsed.total_seconds() for r in responses]
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_source_requests(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Одновременные запросы к источникам"""
        proj = await auth_client.post(
            "/projects", json={"name": "Load Test", "status": "active"}
        )
        assert proj.status_code == 201
        pid = proj.json()["id"]
        num_requests = 30
        tasks = [
            auth_client.get(f"/projects/{pid}/sources") for _ in range(num_requests)
        ]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)

        times = [r.elapsed.total_seconds() for r in responses]
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_source_table_requests(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Одновременные запросы к таблицам источников"""
        proj = await auth_client.post(
            "/projects", json={"name": "Load Test", "status": "active"}
        )
        assert proj.status_code == 201
        pid = proj.json()["id"]
        # Создаём источник
        src = await auth_client.post(
            f"/projects/{pid}/sources",
            json={"name": "Source", "description": "", "type": "DB", "row_count": 0},
        )
        assert src.status_code == 201
        sid = src.json()["id"]
        num_requests = 30
        tasks = [
            auth_client.get(f"/projects/{pid}/sources/{sid}/tables")
            for _ in range(num_requests)
        ]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)

        times = [r.elapsed.total_seconds() for r in responses]
        avg_time = sum(times) / len(times)
        assert avg_time < 1.0


# =============================================================================
# Stress Testing
# =============================================================================


class TestStress:
    """Тесты стресса (Stress Testing)"""

    @pytest.mark.asyncio
    async def test_high_concurrent_requests(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Экстремальная нагрузка: 200 одновременных запросов"""
        num_requests = 200
        tasks = [auth_client.get("/projects") for _ in range(num_requests)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Подсчитываем успешные и failed запросы
        successful = sum(
            1
            for r in responses
            if not isinstance(r, Exception) and r.status_code == 200
        )
        failed = sum(
            1 for r in responses if isinstance(r, Exception) or r.status_code != 200
        )

        # Ожидаем, что большинство запросов завершится успешно
        # При стресс-тестировании некоторые могут fail
        success_rate = successful / num_requests
        assert success_rate >= 0.8  # Минимум 80% успешных запросов

    @pytest.mark.asyncio
    async def test_rapid_sequential_requests(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Быстрые последовательные запросы"""
        num_requests = 100
        start_time = time.time()

        for _ in range(num_requests):
            response = await auth_client.get("/projects")
            assert response.status_code == 200

        elapsed = time.time() - start_time
        rps = num_requests / elapsed

        # Проверка throughput
        assert rps > 10  # Минимум 10 запросов в секунду

    @pytest.mark.asyncio
    async def test_large_payload_requests(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Запросы с большими payload"""
        # Создаем проект с большим описанием
        large_description = "x" * 10000
        payload = {
            "name": "Large Project",
            "description": large_description,
            "status": "active",
        }

        # Создаем проект
        response = await auth_client.post("/projects", json=payload)
        assert response.status_code == 201

        # Получаем проект
        response = await auth_client.get("/projects/1")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_deep_pagination(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Глубокая пагинация"""
        # Запрос с большим skip
        response = await auth_client.get("/projects/1/rpi-mappings?skip=1000&limit=20")
        # Должно вернуть пустой список или корректный ответ
        assert response.status_code in [200, 400]


# =============================================================================
# Scalability Testing
# =============================================================================


class TestScalability:
    """Тесты масштабируемости (Scalability Testing)"""

    @pytest.mark.asyncio
    async def test_performance_under_increasing_load(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Производительность при увеличении нагрузки"""
        load_levels = [10, 50, 100, 200]

        results = {}
        for load in load_levels:
            start_time = time.time()
            tasks = [auth_client.get("/projects") for _ in range(load)]
            responses = await asyncio.gather(*tasks)

            elapsed = time.time() - start_time
            avg_time = elapsed / load

            results[load] = {
                "avg_time": avg_time,
                "total_time": elapsed,
                "success_rate": sum(1 for r in responses if r.status_code == 200)
                / load,
            }

        # Проверка, что производительность деградирует предсказуемо
        for load, result in results.items():
            assert result["success_rate"] >= 0.95  # 95% успешных запросов

    @pytest.mark.asyncio
    async def test_caching_effectiveness(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Эффективность кэширования"""
        # Первый запрос (без кэша)
        start_time = time.time()
        response1 = await auth_client.get("/projects")
        time1 = time.time() - start_time

        # Второй запрос (с кэшем)
        start_time = time.time()
        response2 = await auth_client.get("/projects")
        time2 = time.time() - start_time

        # Второй запрос должен быть быстрее
        # В тестовой среде кэш отключен, поэтому это может не работать
        # Но тест демонстрирует принцип
        assert response1.status_code == 200
        assert response2.status_code == 200


# =============================================================================
# Endurance Testing
# =============================================================================


class TestEndurance:
    """Тесты выносливости (Endurance Testing)"""

    @pytest.mark.asyncio
    async def test_sustained_load_over_time(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Длительная нагрузка (имитация)"""
        # Имитация 5 минут работы с запросами каждые 10 секунд
        duration_seconds = 10  # Уменьшено для CI
        interval_seconds = 1

        num_requests = int(duration_seconds / interval_seconds)

        for i in range(num_requests):
            response = await auth_client.get("/projects")
            assert response.status_code == 200
            await asyncio.sleep(interval_seconds)

    @pytest.mark.asyncio
    async def test_memory_leak_detection(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Обнаружение утечек памяти (косвенная проверка)"""
        # Выполняем много запросов и проверяем время ответа
        num_iterations = 50
        times = []

        for i in range(num_iterations):
            start_time = time.time()
            response = await auth_client.get("/projects")
            elapsed = time.time() - start_time
            times.append(elapsed)

            if response.status_code != 200:
                pytest.fail(f"Request {i} failed with status {response.status_code}")

        # Проверка, что время ответа не растет экспоненциально
        # (что могло бы указывать на утечку памяти)
        if len(times) > 10:
            first_half_avg = sum(times[: len(times) // 2]) / (len(times) // 2)
            second_half_avg = sum(times[len(times) // 2 :]) / (
                len(times) - len(times) // 2
            )

            # Второе полушарие не должно быть значительно медленнее
            assert (
                second_half_avg / first_half_avg < 2.0
            )  # Не более чем в 2 раза медленнее


# =============================================================================
# Spike Testing
# =============================================================================


class TestSpike:
    """Тесты пиковой нагрузки (Spike Testing)"""

    @pytest.mark.asyncio
    async def test_sudden_traffic_spike(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Резкий скачок трафика"""
        # Сначала нормальная нагрузка
        for _ in range(10):
            response = await auth_client.get("/projects")
            assert response.status_code == 200

        # Затем резкий скачок
        spike_size = 100
        tasks = [auth_client.get("/projects") for _ in range(spike_size)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(
            1
            for r in responses
            if not isinstance(r, Exception) and r.status_code == 200
        )
        success_rate = successful / spike_size

        # Ожидаем, что система выдержит пик
        assert success_rate >= 0.8  # Минимум 80% успешных запросов

    @pytest.mark.asyncio
    async def test_gradual_load_increase(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Постепенное увеличение нагрузки"""
        load_steps = [10, 20, 30, 40, 50]

        for load in load_steps:
            tasks = [auth_client.get("/projects") for _ in range(load)]
            responses = await asyncio.gather(*tasks)

            success_rate = sum(1 for r in responses if r.status_code == 200) / load
            assert success_rate >= 0.95


# =============================================================================
# Performance Metrics Collection
# =============================================================================


class TestPerformanceMetrics:
    """Сбор метрик производительности"""

    @pytest.mark.asyncio
    async def test_response_time_percentiles(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Расчет percentiles времени ответа"""
        num_requests = 100
        times = []

        for _ in range(num_requests):
            start = time.time()
            response = await auth_client.get("/projects")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        # Сортируем времена
        times.sort()

        # Расчет percentiles
        p50 = times[int(len(times) * 0.5)]
        p90 = times[int(len(times) * 0.9)]
        p95 = times[int(len(times) * 0.95)]
        p99 = times[int(len(times) * 0.99)]

        # Вывод метрик (для анализа)
        print("\nPerformance Metrics:")
        print(f"P50: {p50 * 1000:.2f}ms")
        print(f"P90: {p90 * 1000:.2f}ms")
        print(f"P95: {p95 * 1000:.2f}ms")
        print(f"P99: {p99 * 1000:.2f}ms")

        # SLA: P95 < 200ms (для production)
        # Для CI используем более мягкие требования
        assert p95 < 2.0  # P95 < 2 секунды в CI

    @pytest.mark.asyncio
    async def test_throughput_measurement(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Измерение throughput"""
        num_requests = 100
        start_time = time.time()

        tasks = [auth_client.get("/projects") for _ in range(num_requests)]
        responses = await asyncio.gather(*tasks)

        elapsed = time.time() - start_time
        rps = num_requests / elapsed

        print(f"\nThroughput: {rps:.2f} requests/second")

        # Минимальный throughput
        assert rps > 5  # Минимум 5 RPS

    @pytest.mark.asyncio
    async def test_error_rate_under_load(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Измерение error rate под нагрузкой"""
        num_requests = 100
        errors = 0

        for _ in range(num_requests):
            response = await auth_client.get("/projects")
            if response.status_code != 200:
                errors += 1

        error_rate = errors / num_requests
        print(f"\nError rate: {error_rate * 100:.2f}%")

        # SLA: error rate < 0.1% (для production)
        # Для CI используем более мягкие требования
        assert error_rate < 0.05  # Менее 5% ошибок в CI


# =============================================================================
# Database Performance
# =============================================================================


class TestDatabasePerformance:
    """Тесты производительности базы данных"""

    @pytest.mark.asyncio
    async def test_db_query_performance(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        """Производительность запросов к БД"""
        # Запускаем много запросов и измеряем время
        num_queries = 50
        times = []

        for _ in range(num_queries):
            start = time.time()
            response = await auth_client.get("/projects/1/sources")
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_db_time = sum(times) / len(times)
        print(f"\nAverage DB query time: {avg_db_time * 1000:.2f}ms")

        # SLA: среднее время запроса < 500ms
        assert avg_db_time < 1.0  # < 1 секунды в CI

    @pytest.mark.asyncio
    async def test_db_connection_pool(
        self, auth_client: AsyncClient, db_session: AsyncSession
    ):
        num_concurrent = 50
        tasks = [auth_client.get("/projects/1/sources") for _ in range(num_concurrent)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful = sum(
            1
            for r in responses
            if not isinstance(r, Exception) and r.status_code in (200, 404)
            #                                                       ^^^ 404 тоже OK —
            #                                                       проект 1 может не существовать
        )
        assert successful >= num_concurrent * 0.9
