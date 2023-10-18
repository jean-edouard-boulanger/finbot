import fnmatch
import io
import logging
import re
from datetime import date, datetime
from ftplib import FTP
from pathlib import Path
from typing import Annotated, Literal, Optional

from pydantic.v1 import BaseModel, Field


class LocalIntakeMethod(BaseModel):
    method_type: Literal["local_file"] = "local_file"
    local_intake_dir: Path


class FtpIntakeMethod(BaseModel):
    method_type: Literal["ftp"] = "ftp"
    ftp_host: str
    port: int = 21
    username: str
    password: str
    directory: str = "outgoing"


IntakeMethodType = LocalIntakeMethod | FtpIntakeMethod
IntakeMethod = Annotated[IntakeMethodType, Field(discriminator="method_type")]


def _extract_report_date_from_file_name(file_name: str) -> date | None:
    match = re.search(r"(2\d{3}[0-1]\d[0-3]\d)\.xml", file_name)
    if not match:
        return None
    raw_date = match.group(1)
    try:
        return datetime.strptime(raw_date, "%Y%m%d").date()
    except ValueError:
        return None


def _find_latest_report_file(available_reports: list[Path]) -> Path | None:
    candidates: list[tuple[Path, date]] = []
    for candidate_report in available_reports:
        if report_date := _extract_report_date_from_file_name(candidate_report.name):
            candidates.append((candidate_report, report_date))
    for candidate_report, _ in reversed(sorted(candidates, key=lambda item: item[1])):
        return candidate_report
    return None


def _load_latest_report_from_local(
    report_file_pattern: str, intake_method: LocalIntakeMethod
) -> Optional[bytes]:
    local_intake_dir = intake_method.local_intake_dir.expanduser().absolute()
    if not local_intake_dir.is_dir():
        raise RuntimeError(
            f"Local intake directory '{local_intake_dir}' does not exist or is not a directory"
        )
    if report_file := _find_latest_report_file(
        list(local_intake_dir.glob(report_file_pattern))
    ):
        return report_file.read_bytes()
    return None


def _load_latest_report_from_ftp(
    report_file_pattern: str, intake_method: FtpIntakeMethod
) -> Optional[bytes]:
    ftp = FTP(
        host=intake_method.ftp_host,
        user=intake_method.username,
        passwd=intake_method.password,
    )
    with ftp:
        ftp.cwd(intake_method.directory)
        report_file = _find_latest_report_file(
            [
                Path(file_name)
                for file_name in ftp.nlst()
                if fnmatch.fnmatch(file_name, report_file_pattern)
            ]
        )
        if report_file:
            logging.debug(f"will download report file {report_file}")
            buffer = io.BytesIO()
            ftp.retrbinary(f"RETR {report_file}", buffer.write)
            return buffer.getvalue()
        return None


def load_latest_report_payload(
    report_file_pattern: str,
    intake_method: IntakeMethodType,
) -> bytes:
    if isinstance(intake_method, LocalIntakeMethod):
        payload = _load_latest_report_from_local(report_file_pattern, intake_method)
    elif isinstance(intake_method, FtpIntakeMethod):
        payload = _load_latest_report_from_ftp(report_file_pattern, intake_method)
    else:
        raise NotImplementedError(f"unsupported intake method: {intake_method}")
    if not payload:
        raise RuntimeError(
            f"no report available from '{intake_method.method_type}' intake"
            f" (report file pattern: {report_file_pattern})"
        )
    return payload
