import pytest
from pydantic import ValidationError

from app.schemas.source_table import SourceColumnBase
from app.schemas.rpi_mapping import RPIMappingBase


def test_source_column_formula_required_if_calculated():
    with pytest.raises(ValidationError):
        SourceColumnBase(
            name="calc_col",
            type="metric",
            data_type="float",
            description="",
            is_calculated=True,
            formula=None,
        )

    col = SourceColumnBase(
        name="calc_col",
        type="metric",
        data_type="float",
        description="",
        is_calculated=True,
        formula="a + b",
    )
    assert col.formula == "a + b"


def test_rpi_mapping_base_formula_required_if_calculated():
    with pytest.raises(ValidationError):
        RPIMappingBase(
            ownership="ФД",
            status="draft",
            block="Блок 1",
            measurement_type="metric",
            is_calculated=True,
            formula=None,
            measurement="Выручка",
            measurement_description="",
            source_report="",
            object_field="revenue",
            source_column_id=None,
            date_added="2024-01-01",
            date_removed=None,
            comment=None,
            verification_file=None,
        )
