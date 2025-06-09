#!/usr/bin/env python3
import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any

from finbot._version import __api_version__


def export_appwsrv_openapi_schema():
    from finbot.apps.appwsrv import appwsrv

    return patch_schema(appwsrv.app.openapi())


def export_finbotwsrv_openapi_schema():
    from finbot.apps.finbotwsrv import finbotwsrv

    return patch_schema(finbotwsrv.app.openapi())


SCHEMA_EXPORTERS = {
    "appwsrv": export_appwsrv_openapi_schema,
    "finbotwsrv": export_finbotwsrv_openapi_schema,
}


def patch_schema(node: Any) -> Any:
    """Under openapi 3.1.0, openapi-generator seems to completely ignore additionalProperties being set to false in
    the schema - which causes significant issues with the generated API. This function translates openapi 3.0.1 features
    to 3.0.3, where openapi-generator behaves nicely.
    """
    if isinstance(node, dict):
        if "openapi" in node:
            node["openapi"] = "3.0.3"
        if "const" in node:
            val = node["const"]
            del node["const"]
            node["enum"] = [val]
        return {k: patch_schema(v) for (k, v) in node.items()}
    if isinstance(node, list):
        return [patch_schema(x) for x in node]
    return node


def create_argument_parser():
    parser = ArgumentParser("Export OpenAPI schema")
    parser.add_argument(
        "-s",
        "--service",
        type=str,
        choices=["appwsrv", "finbotwsrv"],
        required=True,
    )
    parser.add_argument(
        "--show-api-version",
        action="store_true",
        default=False,
        help="Show API version and exists",
    )
    parser.add_argument(
        "-o",
        "--output-file-path",
        type=Path,
        default=None,
    )
    return parser


def main():
    settings = create_argument_parser().parse_args()
    if settings.show_api_version:
        print(__api_version__)
        return
    schema = json.dumps(SCHEMA_EXPORTERS[settings.service](), indent=4)
    if settings.output_file_path:
        settings.output_file_path.expanduser().absolute().write_text(schema)
    else:
        print(schema)


if __name__ == "__main__":
    main()
