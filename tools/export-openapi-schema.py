#!/usr/bin/env python3
import json
from argparse import ArgumentParser
from pathlib import Path

from finbot._version import __api_version__


def export_appwsrv_openapi_schema():
    from finbot.apps.appwsrv import appwsrv

    with appwsrv.app.app_context():
        return appwsrv.spec.spec


def export_finbotwsrv_openapi_schema():
    from finbot.apps.finbotwsrv import finbotwsrv

    with finbotwsrv.app.app_context():
        return finbotwsrv.spec.spec


SCHEMA_EXPORTERS = {
    "appwsrv": export_appwsrv_openapi_schema,
    "finbotwsrv": export_finbotwsrv_openapi_schema,
}


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
