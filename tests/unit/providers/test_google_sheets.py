from typing import Any, Literal

import pytest

from finbot.core.schema import BaseModel
from finbot.providers import google_sheets
from finbot.providers.google_sheets import (
    ACCOUNTS_TABLE_MARKER,
    AccountsTableSchema,
    Cell,
    InvalidSheetData,
    LocalSheet,
    TableEntry,
)
from finbot.providers.schema import AccountType


@pytest.fixture(scope="function")
def sample_sheet():
    return LocalSheet(
        grid=[
            ["", "", "", "", "", ""],
            ["", "ACCOUNTS", "", "", "", ""],
            ["", "identifier", "description", "currency", "type", "sub_type"],
            ["", "Precious metals", "Precious metals", "EUR", "investment", "other"],
            ["", "Cash", "Cash", "EUR", "depository", "checking"],
        ]
    )


class TestLocalSheet:
    def test_rows(self, sample_sheet: LocalSheet):
        assert sample_sheet.rows == 5

    def test_cols(self, sample_sheet: LocalSheet):
        assert sample_sheet.cols == 6

    def test_has_cell(self, sample_sheet: LocalSheet):
        for row_index, row in enumerate(sample_sheet.grid):
            for col_index in range(len(row)):
                assert sample_sheet.has_cell(row_index, col_index)
        assert not sample_sheet.has_cell(len(sample_sheet.grid), 0)

    def test_get_cell(self, sample_sheet: LocalSheet):
        for row_index, row in enumerate(sample_sheet.grid):
            for col_index in range(len(row)):
                cell = sample_sheet.get_cell(row_index, col_index)
                assert cell.row == row_index
                assert cell.col == col_index
                assert cell.val == sample_sheet.grid[row_index][col_index]
        cell = sample_sheet.get_cell(len(sample_sheet.grid), 0)
        assert cell is not None
        assert cell.row == len(sample_sheet.grid)
        assert cell.col == 0
        assert cell.val is None

    def test_find_all(self, sample_sheet: LocalSheet):
        assert sample_sheet.find_all("DOES_NOT_EXIST") == []
        assert sample_sheet.find_all("ACCOUNTS") == [Cell(1, 1, "ACCOUNTS")]
        assert sample_sheet.find_all("EUR") == [
            Cell(3, 3, "EUR"),
            Cell(4, 3, "EUR"),
        ]

    def test_iter_row_cells(self, sample_sheet: LocalSheet):
        cells = list(sample_sheet.iter_row_cells(sample_sheet.get_cell(2, 1)))
        assert cells == [
            Cell(2, 1, "identifier"),
            Cell(2, 2, "description"),
            Cell(2, 3, "currency"),
            Cell(2, 4, "type"),
            Cell(2, 5, "sub_type"),
        ]

    def test_iter_col_cells(self, sample_sheet: LocalSheet):
        cells = list(sample_sheet.iter_col_cells(sample_sheet.get_cell(0, 1)))
        assert cells == [
            Cell(0, 1, ""),
            Cell(1, 1, "ACCOUNTS"),
            Cell(2, 1, "identifier"),
            Cell(3, 1, "Precious metals"),
            Cell(4, 1, "Cash"),
        ]


class TestHelpers:
    @pytest.mark.parametrize(
        "data, expected_payload",
        [
            (None, None),
            ("", None),
            ("key1=value1", {"key1": "value1"}),
            ("key1=value1; key2 = value2", {"key1": "value1", "key2": "value2"}),
            ("key1=value1; type = precious metals", {"key1": "value1", "type": "precious metals"}),
        ],
    )
    def test_parse_provider_specific(
        self,
        data: str | None,
        expected_payload: dict[str, Any] | None,
    ):
        assert google_sheets._parse_provider_specific(data) == expected_payload

    def test_extract_generic_table(
        self,
        sample_sheet: LocalSheet,
    ):
        assert google_sheets._extract_generic_table(
            sheet=sample_sheet,
            marker_cell=sample_sheet.find_all(ACCOUNTS_TABLE_MARKER)[0],
            schema=AccountsTableSchema,
        ) == [
            TableEntry(
                row=3,
                record=AccountsTableSchema(
                    identifier="Precious metals",
                    description="Precious metals",
                    currency="EUR",
                    type=AccountType.investment,
                    sub_type="other",
                ),
            ),
            TableEntry(
                row=4,
                record=AccountsTableSchema(
                    identifier="Cash",
                    description="Cash",
                    currency="EUR",
                    type=AccountType.depository,
                    sub_type="checking",
                ),
            ),
        ]

    def test_extract_generic_table_raises_when_sheet_contains_invalid_data(
        self,
        sample_sheet: LocalSheet,
    ):
        class TestTableSchema(BaseModel):
            type_identifier = "ACCOUNTS"
            name: str
            currency: Literal["USD"]

        with pytest.raises(InvalidSheetData):
            google_sheets._extract_generic_table(
                sheet=sample_sheet,
                marker_cell=sample_sheet.find_all(ACCOUNTS_TABLE_MARKER)[0],
                schema=TestTableSchema,
            )


class TestAccountsTableSchema:
    def test_sub_type_is_null_when_input_value_is_empty_str(self):
        input_payload = {
            "identifier": "acc_1",
            "description": "account 1",
            "currency": "USD",
            "type": "other",
            "sub_type": "",
        }
        table = AccountsTableSchema(**input_payload)
        assert table.sub_type is None
