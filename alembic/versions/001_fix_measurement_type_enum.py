"""fix measurement_type enum values

Revision ID: 001_fix_measurement_type
Revises: 35bc1c36160b
Create Date: 2026-04-20 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_fix_measurement_type'
down_revision: Union[str, Sequence[str], None] = '35bc1c36160b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PostgreSQL не позволяет напрямую изменить enum, поэтому:
    # 1. Создаём новый тип с правильными значениями
    # 2. Конвертируем старые значения в новые
    # 3. Удаляем старый тип
    
    # Создаём новый временный тип
    op.execute("CREATE TYPE measurementtype_new AS ENUM ('dimension', 'metric')")
    
    # Конвертируем данные: 'Измерение' -> 'dimension', 'Метрика' -> 'metric'
    op.execute("""
        ALTER TABLE rpi_mappings 
        ALTER COLUMN measurement_type TYPE measurementtype_new 
        USING CASE 
            WHEN measurement_type = 'Измерение' THEN 'dimension'::measurementtype_new
            WHEN measurement_type = 'Метрика' THEN 'metric'::measurementtype_new
        END
    """)
    
    # Удаляем старый тип
    op.execute("DROP TYPE measurementtype")
    
    # Переименовываем новый тип
    op.execute("ALTER TYPE measurementtype_new RENAME TO measurementtype")


def downgrade() -> None:
    # Обратная конвертация
    op.execute("CREATE TYPE measurementtype_old AS ENUM ('Измерение', 'Метрика')")
    
    op.execute("""
        ALTER TABLE rpi_mappings 
        ALTER COLUMN measurement_type TYPE measurementtype_old 
        USING CASE 
            WHEN measurement_type = 'dimension' THEN 'Измерение'::measurementtype_old
            WHEN measurement_type = 'metric' THEN 'Метрика'::measurementtype_old
        END
    """)
    
    op.execute("DROP TYPE measurementtype")
    op.execute("ALTER TYPE measurementtype_old RENAME TO measurementtype")
