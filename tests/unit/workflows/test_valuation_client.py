from finbot.core.jobs import JobSource
from finbot.workflows.user_account_valuation.client import (
    _make_valuation_job_id,
    parse_valuation_job_owner,
)


def test_job_id_round_trips_to_its_owner() -> None:
    job_id = _make_valuation_job_id(user_account_id=42, job_source=JobSource.app)
    assert parse_valuation_job_owner(job_id) == 42


def test_job_id_owner_survives_different_job_sources() -> None:
    job_id = _make_valuation_job_id(user_account_id=7, job_source=JobSource.schedule)
    assert parse_valuation_job_owner(job_id) == 7


def test_two_jobs_for_the_same_account_do_not_collide() -> None:
    first = _make_valuation_job_id(user_account_id=1, job_source=JobSource.app)
    second = _make_valuation_job_id(user_account_id=1, job_source=JobSource.app)
    assert first != second


def test_malformed_job_id_has_no_owner() -> None:
    assert parse_valuation_job_owner("not-a-job-id") is None
    assert parse_valuation_job_owner("") is None


def test_tampering_with_the_account_segment_changes_the_parsed_owner() -> None:
    """The account id is read straight out of the string with no signature backing it, so this alone is
    NOT what stops account 1 from forging account 2's job id -- it only proves the parser is faithful.
    What actually stops the forgery is that Temporal has no workflow execution under the forged id (a real
    job id is only ever produced by `_make_valuation_job_id`, alongside actually starting that workflow),
    so `get_valuation_job_status` reports it as not found."""
    genuine = _make_valuation_job_id(user_account_id=1, job_source=JobSource.app)
    forged = genuine.replace("valuation-refresh-app-1-", "valuation-refresh-app-2-")
    assert parse_valuation_job_owner(forged) == 2


def test_job_id_with_extra_trailing_content_has_no_owner() -> None:
    genuine = _make_valuation_job_id(user_account_id=1, job_source=JobSource.app)
    assert parse_valuation_job_owner(genuine + "-extra") is None
