from collections import defaultdict
from finbot import providers
from finbot.providers.errors import Error
from oauth2client.service_account import ServiceAccountCredentials
import gspread


class Credentials(object):
    def __init__(self, google_api_credentials, sheet_key):
        self.google_api_credentials = google_api_credentials
        self.sheet_key = sheet_key

    @property
    def user_id(self):
        return str(self.google_api_credentials["client_email"])

    @staticmethod
    def init(data):
        return Credentials(
             data["google_api_credentials"],
             data["sheet_key"])


class Api(providers.Base):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._api = None
        self._sheet = None

    def _iter_accounts(self):
        sheet = LocalSheet(self._sheet.sheet1.get_all_values())

        accounts_table = _get_table(sheet, ACCOUNT_SCHEMA)
        holdings_table = _get_table(sheet, HOLDING_SCHEMA)

        for entry in accounts_table:
            yield {
                "account": {
                    "id": entry["identifier"],
                    "name": entry["description"],
                    "iso_currency": entry["currency"],
                    "type": entry["type"]
                },
                "holdings": [
                    holding for holding in holdings_table
                    if holding["account"] == entry["identifier"]
                ]
            }

    def authenticate(self, credentials: Credentials):
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        self._api = gspread.authorize(
            ServiceAccountCredentials.from_json_keyfile_dict(
                credentials.google_api_credentials, scope))
        self._sheet = self._api.open_by_key(credentials.sheet_key)

    def get_balances(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "balance": sum(holding["value"] for holding in entry["holdings"])
                }
                for entry in self._iter_accounts()
            ]
        }

    def get_assets(self):
        return {
            "accounts": [
                {
                    "account": entry["account"],
                    "assets": [
                        {
                            "name": holding["symbol"],
                            "type": holding["type"],
                            "value": holding["value"]
                        }
                        for holding in entry["holdings"]
                    ]
                }
                for entry in self._iter_accounts()
            ]
        }


class Schema(object):
    def __init__(self, type_identifier, attributes):
        self.type_identifier = type_identifier
        self.attributes = attributes

    def get_type(self, attr):
        return self.attributes[attr]["type"]

    def has_attribute(self, attr):
        return attr in self.attributes

    def is_required(self, attr):
        return attr in self.required_attributes

    @property
    def required_attributes(self):
        return {
            attribute for (attribute, entry)
            in self.attributes.items()
            if entry.get("required", False)
        }


class ValidationError(RuntimeError):
    pass


def union(*values):
    def validate(value):
        if value not in values:
            raise ValidationError(f"should be either {', '.join(values)}")
        return value
    return validate


ACCOUNT_SCHEMA = Schema(
    type_identifier="ACCOUNTS",
    attributes={
        "identifier": {
            "type": str,
            "required": True
        },
        "description": {
            "type": str,
            "required": True
        },
        "currency": {
            "type": str,
            "required": True
        },
        "type": {
            "type": union("cash", "credit", "investment"),
            "required": True
        }
    })


HOLDING_SCHEMA = Schema(
    type_identifier="HOLDINGS",
    attributes={
        "account": {
            "type": str,
            "required": True
        },
        "symbol": {
            "type": str,
            "required": True
        },
        "type": {
            "type": str,
            "required": True
        },
        "units": {
            "type": float,
            "required": True
        },
        "value": {
            "type": float,
            "required": True
        }
    })


class Cell(object):
    def __init__(self, row, col, val):
        self.row = row
        self.col = col
        self.val = val

    def __str__(self):
        return f"Cell(row={self.row+1}, col={self.col+1}, val={self.val})"


class LocalSheet(object):
    def __init__(self, grid):
        self.grid = grid
        self.index = defaultdict(list)
        for cell in self._iter_cells():
            self.index[cell.val].append(cell)

    @property
    def rows(self):
        return len(self.grid)

    @property
    def cols(self):
        return len(self.grid[0])

    def _iter_cells(self):
        for row, cols in enumerate(self.grid):
            for col, val in enumerate(cols):
                yield Cell(row, col, val)

    def iter_row(self, from_cell: Cell):
        row = self.grid[from_cell.row]
        for col in range(from_cell.col, len(row)):
            yield Cell(from_cell.row, col, row[col])

    def iter_col(self, from_cell: Cell):
        for row in range(from_cell.row, len(self.grid)):
            yield Cell(row, from_cell.col, self.grid[row][from_cell.col])

    def has_cell(self, row, col):
        if len(self.grid) == 0:
            return False
        return row < len(self.grid) and col < len(self.grid[0])

    def get_cell(self, row, col):
        if not self.has_cell(row, col):
            return Cell(row, col, None)
        return Cell(row, col, self.grid[row][col])

    def find_all(self, val):
        return self.index[val]

    def find(self, val):
        all_cells = self.find_all(val)
        if len(all_cells) < 1:
            return None
        return all_cells[0]


def _get_table(sheet, schema):
    accounts_marker = schema.type_identifier
    accounts_marker_cell = sheet.find(accounts_marker)
    if not accounts_marker_cell:
        raise Error(f"unable to find '{accounts_marker}' cell")
    return _extract_generic_table(sheet, accounts_marker_cell, schema)


def _extract_generic_table(sheet: LocalSheet, marker_cell: Cell, schema):
    header_start_cell = sheet.get_cell(marker_cell.row + 1, marker_cell.col)
    header = {}
    for cell in sheet.iter_row(from_cell=header_start_cell):
        if cell.val and schema.has_attribute(cell.val):
            header[cell.val] = cell.col
    missing_attributes = schema.required_attributes.difference(set(header.keys()))
    if len(missing_attributes) > 0:
        raise Error(f"missing attribute(s) '{','.join(missing_attributes)}' in header for '{schema.type_identifier}'")

    records = []
    data_start_cell = sheet.get_cell(header_start_cell.row + 1, marker_cell.col)
    for cell in sheet.iter_col(from_cell=data_start_cell):
        if not cell.val:
            break
        current_record = {}
        current_row = cell.row
        for attr, data_col in header.items():
            raw_value = sheet.get_cell(current_row, data_col).val
            if raw_value is None and schema.is_required(attr):
                raise Error(f"cell for required attribute '{schema.type_identifier}.{attr}' is empty")
            converter = schema.get_type(attr)
            try:
                current_record[attr] = converter(raw_value)
            except ValueError:
                raise Error(f"unable to convert value '{raw_value}' to type '{converter.__name__}' "
                            f"for attribute '{schema.type_identifier}.{attr}'")
            except ValidationError as e:
                raise Error(f"unable to convert value '{raw_value}' to type '{converter.__name__}' "
                            f"for attribute '{schema.type_identifier}.{attr}' ({e})")
        missing_attributes = schema.required_attributes.difference(
            set(current_record.keys()))
        if len(missing_attributes) > 0:
            raise Error(f"record is missing required attribute(s) '{', '.join(missing_attributes.keys())}'")
        records.append(current_record)
    return records
