# tests/factories.py
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mapping_table import ColumnType, MappingColumn, MappingTable
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


async def create_mapping_table(
    session: AsyncSession, project: Project, source=None, name="Таблица"
):
    mt = MappingTable(
        name="Таблица",
        description="Тестовая таблица",
        project_id=project.id,
    )
    session.add(mt)
    await session.commit()
    await session.refresh(mt)
    return mt


async def create_mapping_column(
    session: AsyncSession, table: MappingTable, name="customer_id"
):
    col = MappingColumn(
        mapping_table_id=table.id,
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


async def create_rpi(session: AsyncSession, project: Project, column=None):
    rpi = RPIMapping(
        project_id=project.id,
        ownership="Финансовый департамент",
        status=RPIStatus.draft,
        block="Блок 1",
        measurement_type=MeasurementType.metric,
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
