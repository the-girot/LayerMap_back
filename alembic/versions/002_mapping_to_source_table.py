"""mapping_to_source_table

Revision ID: 002
Revises: 5c43b21311b9
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "5c43b21311b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Создать source_tables
    op.create_table(
        "source_tables",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "source_id",
            sa.Integer,
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    # 2. Создать source_columns
    op.create_table(
        "source_columns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "source_table_id",
            sa.Integer,
            sa.ForeignKey("source_tables.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=True),
        sa.Column("data_type", sa.String(50), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_calculated", sa.Boolean, default=False),
        sa.Column("formula", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    # 3. Мигрировать данные: mapping_tables → source_tables
    op.execute(
        """
        INSERT INTO source_tables (id, source_id, name, description, created_at, updated_at)
        SELECT mt.id, s.id, mt.name, mt.description, mt.created_at, mt.updated_at
        FROM mapping_tables mt
        JOIN sources s ON s.mapping_table_id = mt.id
    """
    )
    # 4. Мигрировать данные: mapping_columns → source_columns
    op.execute(
        """
        INSERT INTO source_columns
            (id, source_table_id, name, type, data_type,
             description, is_calculated, formula, created_at)
        SELECT id, mapping_table_id, name, type, data_type,
               description, is_calculated, formula, created_at
        FROM mapping_columns
    """
    )
    # 5. Обновить FK в rpi_mappings
    op.drop_constraint(
        "rpi_mappings_source_column_id_fkey",
        "rpi_mappings",
        type_="foreignkey",
    )
    op.create_foreign_key(
        None,
        "rpi_mappings",
        "source_columns",
        ["source_column_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # 6. Убрать mapping_table_id из sources
    op.drop_constraint(
        "sources_mapping_table_id_fkey",
        "sources",
        type_="foreignkey",
    )
    op.drop_column("sources", "mapping_table_id")
    # 7. Удалить старые таблицы
    op.drop_table("mapping_columns")
    op.drop_table("mapping_tables")


def downgrade() -> None:
    raise NotImplementedError("Downgrade not supported for this migration")
