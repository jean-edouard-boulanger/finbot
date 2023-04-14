import re
from datetime import date, datetime
from ftplib import FTP
from pathlib import Path
from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field


class LocalIntakeMethod(BaseModel):
    method_type: Literal["local_file"] = "local_file"
    local_intake_dir: Path


class FtpIntakeMethod(BaseModel):
    method_type: Literal["ftp"] = "ftp"
    ftp_host: str
    username: str
    password: str


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


def _load_latest_report_from_local(intake_method: LocalIntakeMethod) -> Optional[bytes]:
    local_intake_dir = intake_method.local_intake_dir.expanduser().absolute()
    if not local_intake_dir.is_dir():
        raise RuntimeError(
            f"Local intake directory '{local_intake_dir}' does not exist or is not a directory"
        )
    candidates: list[tuple[Path, date]] = []
    for candidate_file in local_intake_dir.glob("flex*.xml"):
        if report_date := _extract_report_date_from_file_name(candidate_file.name):
            candidates.append((candidate_file, report_date))
    for candidate_file, _ in reversed(sorted(candidates, key=lambda item: item[1])):
        return candidate_file.read_bytes()
    return None


def _load_latest_report_from_ftp(intake_method: FtpIntakeMethod) -> Optional[bytes]:
    ftp = FTP(
        host=intake_method.ftp_host,
        user=intake_method.username,
        passwd=intake_method.password,
    )
    ftp.quit()
    raise NotImplementedError()


def load_latest_report_payload(
    intake_method: IntakeMethodType,
) -> bytes:
    if isinstance(intake_method, LocalIntakeMethod):
        payload = _load_latest_report_from_local(intake_method)
    elif isinstance(intake_method, FtpIntakeMethod):
        payload = _load_latest_report_from_ftp(intake_method)
    else:
        raise NotImplementedError(f"unsupported intake method: {intake_method}")
    if not payload:
        raise RuntimeError(
            f"no report available from '{intake_method.method_type}' intake"
        )
    return payload
