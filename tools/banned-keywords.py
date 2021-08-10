#!/usr/bin/env python3
from typing import Optional, Pattern
from pathlib import Path
from dataclasses import dataclass
import argparse
import fnmatch
import re
import sys
import os


@dataclass
class Rule:
    match_files: list[str]
    banned_pattern: Pattern[str]
    message: Optional[str] = None
    ignore_files: Optional[list[str]] = None


RULES: list[Rule] = [
    Rule(
        match_files=["*.py"],
        banned_pattern=re.compile(r"find_elements_by_[^(]+"),
        message="Selenium find_elements_by_* commands are deprecated. "
        "Please use find_elements(...) instead.",
    ),
    Rule(
        match_files=["*.py"],
        banned_pattern=re.compile(r"find_element_by_[^(]+"),
        message="Selenium find_element_by_* commands are deprecated. "
        "Please use find_element(...) instead.",
    ),
    Rule(
        match_files=["*.py"],
        banned_pattern=re.compile(r"import(.+)(List|(?<!Typed)Dict)|Dict\[|List\["),
        message="As of python3.9, dict and list type hints may be used installed of Dict and List",
    ),
    Rule(
        match_files=["*.py"],
        ignore_files=["finbot/core/web_service.py"],
        banned_pattern=re.compile(r"jsonify\("),
        message="Finbot web services should not call Flask jsonify"
        " (this is automatically done upstream)",
    ),
    Rule(
        match_files=["*.py"],
        ignore_files=["finbot/core/utils.py"],
        banned_pattern=re.compile("stackprinter"),
        message="Please use utils.format_stack instead of stackprinter",
    ),
    Rule(
        match_files=["*.js"],
        banned_pattern=re.compile(r"console.log\("),
        message="Please remove calls to console.log"
    )
]


@dataclass
class Error:
    file_path: Path
    line: str
    line_number: int
    start_column: int
    end_column: int
    error_message: str


def check_source_file(file_path: Path, rules: list[Rule]) -> list[Error]:
    errors = []
    with file_path.open() as cf:
        for line_index, line in enumerate(cf.readlines()):
            for rule in rules:
                for match in rule.banned_pattern.finditer(line):
                    errors.append(
                        Error(
                            file_path=file_path.absolute(),
                            line=line,
                            line_number=line_index + 1,
                            start_column=match.start(),
                            end_column=match.end(),
                            error_message=rule.message,
                        )
                    )
    return errors


def file_matches_any_pattern(file_path: Path, patterns: Optional[list[str]]):
    if not patterns:
        return None
    for pattern in patterns:
        if fnmatch.fnmatch(str(file_path), pattern):
            return True
        return False


def should_match_file_against_rule(file_path: Path, rule: Rule):
    return file_matches_any_pattern(
        file_path, rule.match_files
    ) and not file_matches_any_pattern(file_path, rule.ignore_files)


def handle_source_file(file_path: Path) -> list[Error]:
    errors = []
    matching_rules = []
    for rule in RULES:
        if should_match_file_against_rule(file_path, rule):
            matching_rules.append(rule)
    if matching_rules:
        errors += check_source_file(file_path, matching_rules)
    return errors


def handle_source_dir(source_dir: Path) -> list[Error]:
    errors: list[Error] = []
    for file_path in source_dir.rglob("*"):
        if file_path.is_file():
            errors += handle_source_file(file_path)
    return errors


def create_arguments_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dirs", nargs="+", action="extend", required=True, default=[]
    )
    return parser


def is_github_action() -> bool:
    return "GITHUB_ACTIONS" in os.environ


def display_error_message(error: Error):
    relative_path = error.file_path.relative_to(Path.cwd())
    print(
        f"{relative_path}:"
        f"{error.line_number}:"
        f"{error.start_column}: "
        f"error: {error.error_message}"
    )
    if is_github_action():
        print(
            f"::error file={relative_path},"
            f"line={error.line_number},"
            f"col={error.start_column}::"
            f"{error.error_message}"
        )


def main():
    settings = create_arguments_parser().parse_args()
    errors: list[Error] = []
    for source_dir in settings.source_dirs:
        errors += handle_source_dir(Path(source_dir))
    if errors:
        for error in errors:
            display_error_message(error)
            print(f"{error.line_number} | {error.line.rstrip()}")
            spacing = len(f"{error.line_number} | ") + error.start_column
            print(
                (" " * spacing)
                + "^"
                + ("~" * (error.end_column - error.start_column - 2))
                + "+"
            )
            print()
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
