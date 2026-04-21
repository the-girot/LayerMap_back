"""init

Revision ID: 94aca1390145
Revises: 
Create Date: 2026-04-17 13:25:03.970536
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '94aca1390145'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. projects
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('active', 'draft', 'archived', name='projectstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. sources (без FK на mapping_tables пока)
    op.create_table('sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('mapping_table_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('API', 'DB', 'FILE', 'STREAM', name='sourcetype'), nullable=False),
        sa.Column('row_count', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('last_updated', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. mapping_tables (зависит от projects и sources)
    op.create_table('mapping_tables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. circular FK: sources → mapping_tables
    op.create_foreign_key(
        'fk_sources_mapping_table',
        'sources', 'mapping_tables',
        ['mapping_table_id'], ['id'],
        ondelete='SET NULL'
    )

    # 5. mapping_columns
    op.create_table('mapping_columns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mapping_table_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.Enum('dimension', 'metric', name='columntype'), nullable=False),
        sa.Column('data_type', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_calculated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['mapping_table_id'], ['mapping_tables.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. rpi_mappings
    op.create_table('rpi_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('source_column_id', sa.Integer(), nullable=True),
        sa.Column('ownership', sa.String(length=128), nullable=True),
        sa.Column('status', sa.Enum('approved', 'in_review', 'draft', name='rpistatus'), nullable=False),
        sa.Column('block', sa.String(length=128), nullable=True),
        sa.Column('measurement_type', sa.Enum('Измерение', 'Метрика', name='measurementtype'), nullable=False),
        sa.Column('is_calculated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('measurement', sa.String(length=255), nullable=False),
        sa.Column('measurement_description', sa.Text(), nullable=True),
        sa.Column('source_report', sa.String(length=255), nullable=True),
        sa.Column('object_field', sa.String(length=255), nullable=False),
        sa.Column('date_added', sa.Date(), nullable=True),
        sa.Column('date_removed', sa.Date(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('verification_file', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint(
            '(is_calculated = TRUE AND formula IS NOT NULL) OR (is_calculated = FALSE)',
            name='chk_formula'
        ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_column_id'], ['mapping_columns.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 7. Индексы
    op.create_index('idx_sources_project_id', 'sources', ['project_id'])
    op.create_index('idx_mapping_tables_project_id', 'mapping_tables', ['project_id'])
    op.create_index('idx_mapping_columns_table_id', 'mapping_columns', ['mapping_table_id'])
    op.create_index('idx_rpi_mappings_project_id', 'rpi_mappings', ['project_id'])
    op.create_index('idx_rpi_mappings_status', 'rpi_mappings', ['status'])
    op.create_index('idx_rpi_mappings_ownership', 'rpi_mappings', ['ownership'])
    op.create_index('idx_rpi_mappings_type', 'rpi_mappings', ['measurement_type'])


def downgrade() -> None:
    op.drop_index('idx_rpi_mappings_type')
    op.drop_index('idx_rpi_mappings_ownership')
    op.drop_index('idx_rpi_mappings_status')
    op.drop_index('idx_rpi_mappings_project_id')
    op.drop_index('idx_mapping_columns_table_id')
    op.drop_index('idx_mapping_tables_project_id')
    op.drop_index('idx_sources_project_id')
    op.drop_table('rpi_mappings')
    op.drop_table('mapping_columns')
    op.drop_constraint('fk_sources_mapping_table', 'sources', type_='foreignkey')
    op.drop_table('mapping_tables')
    op.drop_table('sources')
    op.drop_table('projects')
    op.execute('DROP TYPE IF EXISTS measurementtype')
    op.execute('DROP TYPE IF EXISTS rpistatus')
    op.execute('DROP TYPE IF EXISTS columntype')
    op.execute('DROP TYPE IF EXISTS sourcetype')
    op.execute('DROP TYPE IF EXISTS projectstatus')