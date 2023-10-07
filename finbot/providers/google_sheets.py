from collections import defaultdict
from typing import (
    Any,
    Callable,
    Generator,
    Iterator,
    Optional,
    Type,
    TypedDict,
    TypeVar,
    Union,
)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydantic import BaseModel

from finbot.core.errors import FinbotError
from finbot.providers.base import ProviderBase
from finbot.providers.errors import AuthenticationFailure
from finbot.providers.schema import (
    Account,
    Asset,
    AssetClass,
    Assets,
    AssetsEntry,
    BalanceEntry,
    Balances,
    CurrencyCode,
)


class Error(FinbotError):
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
        self._api: Optional[gspread.Client] = None
        self._sheet: Optional[gspread.Spreadsheet] = None

    def _iter_accounts(self) -> Generator[AssetsEntry, None, None]:
        assert self._sheet is not None
        sheet = LocalSheet(self._sheet.sheet1.get_all_values())

        accounts_table = _get_table(sheet, ACCOUNT_SCHEMA)
        holdings_table = _get_table(sheet, HOLDING_SCHEMA)

        for entry in accounts_table:
            yield AssetsEntry(
                account=Account(
                    id=entry["identifier"],
                    name=entry["description"],
                    iso_currency=entry["currency"],
                    type=entry["type"],
                ),
                assets=[
                    Asset(
                        name=holding["symbol"],
                        type=holding["type"],
                        asset_class=_parse_asset_class(holding.get("asset_class")),
                        value=holding["value"],
                        provider_specific=_parse_provider_specific(
                            holding.get("custom")
                        ),
                    )
                    for holding in holdings_table
                    if holding["account"] == entry["identifier"]
                ],
            )

    def initialize(self) -> None:
        try:
            scope = ["https://www.googleapis.com/auth/spreadsheets"]
            self._api = gspread.authorize(
                ServiceAccountCredentials.from_json_keyfile_dict(
                    self._credentials.google_api_credentials, scope
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


class AttributeDef(TypedDict):
    type: Union[Callable[[Optional[str]], Any], Type[Any]]
    required: bool


class Schema(object):
    def __init__(
        self, type_identifier: str, attributes: dict[str, AttributeDef]
    ) -> None:
        self.type_identifier = type_identifier
        self.attributes = attributes

    def get_type(self, attr: str) -> Callable[[Optional[str]], Any]:
        return self.attributes[attr]["type"]

    def has_attribute(self, attr: str) -> bool:
        return attr in self.attributes

    def is_required(self, attr: str) -> bool:
        return attr in self.required_attributes

    @property
    def required_attributes(self) -> set[str]:
        return {
            attribute
            for (attribute, entry) in self.attributes.items()
            if entry.get("required", False)
        }


class ValidationError(RuntimeError):
    pass


def union(*values: str) -> Callable[[Optional[str]], Optional[str]]:
    def impl(value: Optional[str]) -> Optional[str]:
        if value not in values:
            raise ValidationError(f"should be either {', '.join(values)}")
        return value

    return impl


T = TypeVar("T")


def optional(t: type[T]) -> Callable[[Optional[str]], Optional[T]]:
    def impl(value: Optional[str]) -> Optional[T]:
        if value is None or value.lower() in ("", "null", "none", "n/a"):
            return None
        return t(value)  # type: ignore

    return impl


ACCOUNT_SCHEMA = Schema(
    type_identifier="ACCOUNTS",
    attributes={
        "identifier": {"type": str, "required": True},
        "description": {"type": str, "required": True},
        "currency": {"type": str, "required": True},
        "type": {"type": union("cash", "credit", "investment"), "required": True},
    },
)


HOLDING_SCHEMA = Schema(
    type_identifier="HOLDINGS",
    attributes={
        "account": {"type": str, "required": True},
        "symbol": {"type": str, "required": True},
        "type": {"type": str, "required": True},
        "asset_class": {"type": optional(str), "required": False},
        "units": {"type": optional(float), "required": True},
        "value": {"type": float, "required": True},
        "custom": {"type": str, "required": False},
    },
)


class Cell(object):
    def __init__(self, row: int, col: int, val: Optional[str]):
        self.row = row
        self.col = col
        self.val = val

    def __str__(self) -> str:
        return f"Cell(row={self.row+1}, col={self.col+1}, val={self.val})"


class LocalSheet(object):
    def __init__(self, grid: list[list[str]]) -> None:
        self.grid = grid
        self.index: defaultdict[Optional[str], list[Cell]] = defaultdict(list)
        for cell in self._iter_cells():
            self.index[cell.val].append(cell)

    @property
    def rows(self) -> int:
        return len(self.grid)

    @property
    def cols(self) -> int:
        return len(self.grid[0])

    def _iter_cells(self) -> Iterator[Cell]:
        for row, cols in enumerate(self.grid):
            for col, val in enumerate(cols):
                yield Cell(row, col, val)

    def iter_row(self, from_cell: Cell) -> Iterator[Cell]:
        row = self.grid[from_cell.row]
        for col in range(from_cell.col, len(row)):
            yield Cell(from_cell.row, col, row[col])

    def iter_col(self, from_cell: Cell) -> Iterator[Cell]:
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

    def find(self, val: str) -> Optional[Cell]:
        all_cells = self.find_all(val)
        if len(all_cells) < 1:
            return None
        return all_cells[0]


def _extract_generic_table(
    sheet: LocalSheet, marker_cell: Cell, schema: Schema
) -> list[dict[Any, Any]]:
    header_start_cell = sheet.get_cell(marker_cell.row + 1, marker_cell.col)
    header = {}
    for cell in sheet.iter_row(from_cell=header_start_cell):
        if cell.val and schema.has_attribute(cell.val):
            header[cell.val] = cell.col
    missing_attributes = schema.required_attributes.difference(set(header.keys()))
    if len(missing_attributes) > 0:
        raise Error(
            f"missing attribute(s) '{','.join(missing_attributes)}'"
            f" in header for '{schema.type_identifier}'"
        )

    records = []
    data_start_cell = sheet.get_cell(header_start_cell.row + 1, marker_cell.col)
    for cell in sheet.iter_col(from_cell=data_start_cell):
        if not cell.val:
            break
        current_record: dict[str, Any] = {}
        current_row = cell.row
        for attr, data_col in header.items():
            raw_value = sheet.get_cell(current_row, data_col).val
            if raw_value is None and schema.is_required(attr):
                raise Error(
                    f"cell for required attribute '{schema.type_identifier}.{attr}' is empty"
                )
            converter = schema.get_type(attr)
            try:
                current_record[attr] = converter(raw_value)
            except ValueError:
                raise Error(
                    f"unable to convert value '{raw_value}' to type '{converter.__name__}' "
                    f"for attribute '{schema.type_identifier}.{attr}'"
                )
            except ValidationError as e:
                raise Error(
                    f"unable to convert value '{raw_value}' to type '{converter.__name__}' "
                    f"for attribute '{schema.type_identifier}.{attr}' ({e})"
                )
        missing_attributes = schema.required_attributes.difference(
            set(current_record.keys())
        )
        if len(missing_attributes) > 0:
            raise Error(
                f"record is missing required attribute(s) '{', '.join(missing_attributes)}'"
            )
        records.append(current_record)
    return records


def _get_table(sheet: LocalSheet, schema: Schema) -> list[dict[Any, Any]]:
    marker = schema.type_identifier
    marker_cell = sheet.find(marker)
    if not marker_cell:
        raise Error(f"unable to find '{marker}' cell")
    return _extract_generic_table(sheet, marker_cell, schema)


def _parse_provider_specific(data: str | None) -> dict[str, Any] | None:
    provider_specific = {}
    if not data:
        return None
    entries = data.split(";")
    for entry in entries:
        key, value = entry.split("=")
        provider_specific[key.strip()] = value.strip()
    return provider_specific


def _parse_asset_class(data: str | None) -> AssetClass | None:
    if not data:
        return None
    items = data.split("_")
    raw_asset_class = "".join(item.capitalize() for item in items)
    return AssetClass[raw_asset_class]
