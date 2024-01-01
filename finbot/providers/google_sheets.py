from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Generator, Literal, TypedDict, TypeVar, cast

import gspread
from gspread.utils import rowcol_to_a1
from oauth2client.service_account import ServiceAccountCredentials
from pydantic.v1 import ValidationError as PydanticValidationError

from finbot.core.schema import BaseModel, CurrencyCode
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure, ProviderError
from finbot.providers.schema import (
    Account,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    AssetType,
    BalanceEntry,
    Balances,
)

SchemaNamespace = "GoogleSheetsProvider"


ACCOUNTS_TABLE_MARKER = "ACCOUNTS"
HOLDINGS_TABLE_MARKER = "HOLDINGS"


class Error(ProviderError):
    def __init__(self, error_message: str):
        super().__init__(error_message, "PGS1")


class InvalidSheetData(Error):
    def __init__(self, error_message: str):
        super().__init__(error_message)


class GoogleApiCredentials(TypedDict):
    type: str
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str
    token_uri: str
    auth_provider_x509_cert_url: str
    client_x509_cert_url: str


class Credentials(BaseModel):
    sheet_key: str
    google_api_credentials: GoogleApiCredentials


TableSchemaT = TypeVar("TableSchemaT", bound=BaseModel)


class AccountsTableSchema(BaseModel):
    identifier: str
    description: str
    currency: str
    type: Literal["cash", "credit", "investment"]


class HoldingsTableSchema(BaseModel):
    account: str
    symbol: str
    type: str | None
    asset_class: AssetClass
    asset_type: AssetType
    units: float | None
    value: float
    underlying_ccy: str | None
    custom: str | None

    @property
    def provider_specific(self) -> dict[str, Any] | None:
        return _parse_provider_specific(self.custom)


class Api(ProviderBase):
    description = "Google sheets"
    credentials_type = Credentials

    def __init__(
        self,
        credentials: Credentials,
        user_account_currency: CurrencyCode,
        **kwargs: Any,
    ) -> None:
        super().__init__(user_account_currency=user_account_currency, **kwargs)
        self._credentials = credentials
        self._api: gspread.Client | None = None
        self._sheet: gspread.Spreadsheet | None = None

    @staticmethod
    def _make_asset(holding: HoldingsTableSchema) -> Asset:
        return Asset(
            name=holding.symbol,
            type=holding.type or f"{holding.asset_class.value} {holding.asset_type.value}",
            asset_class=holding.asset_class,
            asset_type=holding.asset_type,
            value=holding.value,
            provider_specific=holding.provider_specific,
            underlying_ccy=CurrencyCode(holding.underlying_ccy.upper()) if holding.underlying_ccy else None,
        )

    def _iter_accounts(self) -> Generator[AssetsEntry, None, None]:
        assert self._sheet is not None
        sheet = LocalSheet(self._sheet.sheet1.get_all_values())

        accounts_table = _get_table(sheet, ACCOUNTS_TABLE_MARKER, AccountsTableSchema)
        holdings_table = _get_table(sheet, HOLDINGS_TABLE_MARKER, HoldingsTableSchema)

        for account in accounts_table:
            yield AssetsEntry(
                account=Account(
                    id=account.identifier,
                    name=account.description,
                    iso_currency=CurrencyCode(account.currency.upper()),
                    type=account.type,
                ),
                assets=[
                    self._make_asset(holding) for holding in holdings_table if holding.account == account.identifier
                ],
            )

    def initialize(self) -> None:
        try:
            self._api = gspread.authorize(
                ServiceAccountCredentials.from_json_keyfile_dict(
                    keyfile_dict=self._credentials.google_api_credentials,
                    scopes=["https://www.googleapis.com/auth/spreadsheets"],
                )
            )
            self._sheet = self._api.open_by_key(self._credentials.sheet_key)
        except Exception as e:
            raise AuthenticationFailure(str(e)) from e

    def get_balances(self) -> Balances:
        return Balances(
            accounts=[
                BalanceEntry(
                    account=entry.account,
                    balance=sum(asset.value for asset in entry.assets),
                )
                for entry in self._iter_accounts()
            ]
        )

    def get_assets(self) -> Assets:
        return Assets(accounts=list(self._iter_accounts()))


@dataclass(frozen=True)
class Cell(object):
    row: int
    col: int
    val: str | None

    def __post_init__(self) -> None:
        assert self.row >= 0 and self.col >= 0, f"invalid cell coordinates: ({self.row}, self.col)"

    @property
    def pretty_loc(self) -> str:
        return cast(str, rowcol_to_a1(self.row + 1, self.col + 1))


class LocalSheet(object):
    def __init__(self, grid: list[list[str]]) -> None:
        self.grid = grid
        self.index: defaultdict[str | None, list[Cell]] = defaultdict(list)
        for cell in self._iter_cells():
            self.index[cell.val].append(cell)

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])

    def _iter_cells(self) -> Generator[Cell, None, None]:
        for row, cols in enumerate(self.grid):
            for col, val in enumerate(cols):
                yield Cell(row, col, val)

    def iter_row_cells(self, from_cell: Cell) -> Generator[Cell, None, None]:
        row = self.grid[from_cell.row]
        for col in range(from_cell.col, len(row)):
            yield Cell(from_cell.row, col, row[col])

    def iter_col_cells(self, from_cell: Cell) -> Generator[Cell, None, None]:
        for row in range(from_cell.row, len(self.grid)):
            yield Cell(row, from_cell.col, self.grid[row][from_cell.col])

    def has_cell(self, row: int, col: int) -> bool:
        if len(self.grid) == 0:
            return False
        return row < len(self.grid) and col < len(self.grid[0])

    def get_cell(self, row: int, col: int) -> Cell:
        if not self.has_cell(row, col):
            return Cell(row, col, None)
        return Cell(row, col, self.grid[row][col])

    def find_all(self, val: str) -> list[Cell]:
        return self.index[val]


def _extract_generic_table(
    sheet: LocalSheet,
    marker_cell: Cell,
    schema: type[TableSchemaT],
) -> list[TableSchemaT]:
    header_start_cell = sheet.get_cell(marker_cell.row + 1, marker_cell.col)
    header = {}
    for cell in sheet.iter_row_cells(from_cell=header_start_cell):
        if cell.val and cell.val in schema.__fields__:
            header[cell.val] = cell.col
    records: list[TableSchemaT] = []
    data_start_cell = sheet.get_cell(header_start_cell.row + 1, marker_cell.col)
    for cell in sheet.iter_col_cells(from_cell=data_start_cell):
        if not cell.val:
            break
        current_row = cell.row
        record_payload = {attr: sheet.get_cell(current_row, data_col_idx).val for attr, data_col_idx in header.items()}
        try:
            record = schema(**record_payload)
        except PydanticValidationError as e:
            pretty_validation_error = _format_record_validation_error(e)
            pretty_row = ";".join(cell.val or "" for cell in sheet.iter_row_cells(cell))
            pretty_entry = ", ".join(f"{key}='{val}'" for (key, val) in record_payload.items())
            raise InvalidSheetData(
                f"Invalid '{marker_cell.val}' table entry ({pretty_entry}) at row {current_row + 1} ({pretty_row}):"
                f" {pretty_validation_error}"
            ) from e
        records.append(record)
    return records


def _format_record_validation_error(e: PydanticValidationError) -> str:
    pretty_errors = []
    for error in e.errors():
        pretty_loc = ", ".join(f"'{entry}'" for entry in error["loc"])
        pretty_errors.append(f"{pretty_loc} {error["msg"]}")
    return ", ".join(pretty_errors)


def _get_table(
    sheet: LocalSheet,
    table_marker: str,
    schema: type[TableSchemaT],
) -> list[TableSchemaT]:
    marker_cells = sheet.find_all(table_marker)
    if not marker_cells:
        raise InvalidSheetData(f"Unable to find cell with text '{table_marker}' in the sheet")
    if len(marker_cells) > 1:
        pretty_cells = ", ".join(cell.pretty_loc for cell in marker_cells)
        raise InvalidSheetData(
            f"Found multiple cells ({pretty_cells}) with text '{table_marker}' in the sheet."
            f" Only one table of type '{table_marker}' was expected."
        )
    return _extract_generic_table(sheet, marker_cells[0], schema)


def _parse_provider_specific(data: str | None) -> dict[str, Any] | None:
    provider_specific = {}
    if not data:
        return None
    entries = data.split(";")
    for entry in entries:
        key, value = entry.split("=")
        provider_specific[key.strip()] = value.strip()
    return provider_specific
