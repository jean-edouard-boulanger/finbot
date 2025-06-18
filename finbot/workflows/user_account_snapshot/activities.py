from dataclasses import dataclass

from temporalio import activity

from finbot.core.schema import CurrencyCode
from finbot.core.utils import some
from finbot.workflows.user_account_snapshot import schema


@activity.defn(name="create_empty_snapshot")
def create_empty_snapshot(user_account_id: int) -> schema.SnapshotMetadata:
    from finbot.model import ScopedSession
    from finbot.workflows.user_account_snapshot.impl import create_empty_snapshot

    with ScopedSession() as session:
        snapshot = create_empty_snapshot(user_account_id, session)
        return schema.SnapshotMetadata(
            id=snapshot.id,
            user_account_id=user_account_id,
            requested_ccy=CurrencyCode(snapshot.requested_ccy),
        )


@activity.defn(name="prepare_raw_snapshot_requests")
def prepare_raw_snapshot_requests(
    request: schema.TakeRawSnapshotRequest,
) -> list[schema.LinkedAccountSnapshotRequest]:
    from finbot.model import ScopedSession
    from finbot.workflows.user_account_snapshot import impl

    with ScopedSession() as session:
        return impl.prepare_raw_snapshot_requests(
            user_account=impl.load_user_account(request.user_account_id, session),
            linked_account_ids=request.linked_account_ids,
        )


@dataclass(frozen=True)
class BuildAndPersistFinalSnapshotActivityRequest:
    snapshot_meta: schema.SnapshotMetadata
    raw_snapshot: list[schema.LinkedAccountSnapshotResponse]


@activity.defn(name="build_and_persist_final_snapshot")
def build_and_persist_final_snapshot(
    request: BuildAndPersistFinalSnapshotActivityRequest,
) -> schema.SnapshotSummary:
    from finbot.model import ScopedSession, UserAccountSnapshot
    from finbot.workflows.user_account_snapshot import impl

    with ScopedSession() as db_session:
        return impl.build_and_persist_final_snapshot(
            user_account=impl.load_user_account(request.snapshot_meta.user_account_id, db_session),
            new_snapshot=some(db_session.query(UserAccountSnapshot).get(request.snapshot_meta.id)),
            raw_snapshot=request.raw_snapshot,
            db_session=db_session,
        )
