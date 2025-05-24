#!/usr/bin/env python3
import importlib
import inspect
import sys
import typing as t
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import finbot
from finbot.core.pydantic_ import BaseModel
from finbot.core.spec_tree import get_model_key


@dataclass
class SchemaEntry:
    schema_type: type[BaseModel]
    module_name: str
    module_file_path: Path


def lenient_issubclass(t: type, cls: type) -> bool:
    try:
        return issubclass(t, cls)
    except TypeError:
        return False


def iter_module_schemas(module_name: str) -> t.Generator[type[BaseModel], None, None]:
    module = importlib.import_module(module_name)
    for val in module.__dict__.values():
        if lenient_issubclass(val, BaseModel):
            yield val


def main():
    finbot_root_package_name = finbot.__name__
    finbot_root_package_dir = Path(finbot.__file__).parent.absolute()
    model_keys_schemas: dict[str, list[SchemaEntry]] = defaultdict(list)
    for module_file_path in finbot_root_package_dir.rglob("*.py"):
        module_file_rel_path = module_file_path.relative_to(finbot_root_package_dir)
        parts = tuple(part.replace(".py", "") for part in module_file_rel_path.parts if part != "__init__.py")
        module_name = ".".join((finbot_root_package_name,) + parts)
        for schema_type in iter_module_schemas(module_name):
            schema_module = inspect.getmodule(schema_type)
            if Path(schema_module.__file__) == module_file_path:
                model_keys_schemas[get_model_key(schema_type)].append(
                    SchemaEntry(
                        schema_type=schema_type,
                        module_name=module_name,
                        module_file_path=module_file_path,
                    )
                )
    schema_valid = True
    for model_key, entries in model_keys_schemas.items():
        if len(entries) > 1:
            schema_valid = False
            module_names = ", ".join(entry.module_name for entry in entries)
            print(f"ERROR: schema type '{model_key}' is defined in multiple modules: {module_names}")
    if schema_valid:
        print("Schema is valid")
    return 0 if schema_valid else 1


if __name__ == "__main__":
    sys.exit(main())
