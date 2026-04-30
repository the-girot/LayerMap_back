# tests/factories.py
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source_table import ColumnType, SourceColumn, SourceTable
from app.models.project import Project, ProjectStatus
from app.models.rpi_mapping import MeasurementType, RPIMapping, RPIStatus
from app.models.source import Source, SourceType


async def create_project(
    session: AsyncSession, name="Проект А", status=ProjectStatus.active
):
    project = Project(name=name, description="Тестовый проект", status=status)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def create_source(
    session: AsyncSession, project: Project, name="Источник", type_=SourceType.DB
):
    src = Source(
        project_id=project.id,
        name=name,
        description="Тестовый источник",
        type=type_,
        row_count=0,
    )
    session.add(src)
    await session.commit()
    await session.refresh(src)
    return src


async def create_source_table(
    session: AsyncSession, source: Source, name="Таблица"
):
    st = SourceTable(
        name=name,
        description="Тестовая таблица",
        source_id=source.id,
    )
    session.add(st)
    await session.commit()
    await session.refresh(st)
    return st


async def create_source_column(
    session: AsyncSession, table: SourceTable, name="customer_id"
):
    col = SourceColumn(
        source_table_id=table.id,
        name=name,
        type=ColumnType.dimension,
        data_type="integer",
        description="ID клиента",
        is_calculated=False,
        formula=None,
    )
    session.add(col)
    await session.commit()
    await session.refresh(col)
    return col


async def create_dwh_table(
    session: AsyncSession,
    project: Project,
    layer: str = "STG",
    name: str = "dwh_table",
):
    """Создать DWH-таблицу."""
    from app.models.dwh import DWHLayer, DWHTable

    tbl = DWHTable(
        project_id=project.id,
        layer=DWHLayer(layer),
        name=name,
        description="Тестовая DWH-таблица",
    )
    session.add(tbl)
    await session.commit()
    await session.refresh(tbl)
    return tbl


async def create_dwh_column(
    session: AsyncSession, table, name="col_1", data_type="integer"
):
    """Создать колонку в DWH-таблице."""
    from app.models.dwh import DWHColumn

    col = DWHColumn(
        dwh_table_id=table.id,
        name=name,
        data_type=data_type,
        description="Тестовая колонка",
        is_calculated=False,
        formula=None,
    )
    session.add(col)
    await session.commit()
    await session.refresh(col)
    return col


async def create_layer_mapping(
    session: AsyncSession,
    project: Project,
    target_table,
    source_tables: list,
    transformation: str | None = None,
    algorithm: str | None = None,
):
    """Создать маппинг с источниками."""
    from app.models.dwh import LayerMapping, LayerMappingSource

    mapping = LayerMapping(
        project_id=project.id,
        target_table_id=target_table.id,
        transformation=transformation,
        algorithm=algorithm,
    )
    session.add(mapping)
    await session.flush()

    for st in source_tables:
        lms = LayerMappingSource(
            mapping_id=mapping.id,
            source_table_id=st.id,
        )
        session.add(lms)

    await session.commit()
    await session.refresh(mapping)
    return mapping


async def create_rpi(session: AsyncSession, project: Project, column=None, dimension=None):
    rpi = RPIMapping(
        project_id=project.id,
        ownership="Финансовый департамент",
        status=RPIStatus.draft,
        block="Блок 1",
        measurement_type=MeasurementType.metric,
        dimension=dimension,
        is_calculated=False,
        formula=None,
        measurement="Выручка",
        measurement_description="Общая выручка",
        source_report="Отчёт 123",
        object_field="revenue",
        source_column_id=column.id if column else None,
        date_added=date.today(),
        date_removed=None,
        comment="В работе",
        verification_file=None,
    )
    session.add(rpi)
    await session.commit()
    await session.refresh(rpi)
    return rpi
