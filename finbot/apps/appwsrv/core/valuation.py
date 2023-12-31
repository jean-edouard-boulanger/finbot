import logging

from finbot.apps.appwsrv.db import db_session
from finbot.model import repository
from finbot.services.user_account_valuation import ValuationRequest
from finbot.tasks import user_account_valuation

logger = logging.getLogger(__name__)


def trigger_valuation(user_account_id: int, linked_account_ids: list[int] | None = None) -> None:
    logger.info(f"triggering valuation for account_id={user_account_id} linked_account_ids={linked_account_ids}")
    account = repository.get_user_account(db_session, user_account_id)
    user_account_valuation.client.run_async(
        request=ValuationRequest(
            user_account_id=account.id,
            linked_accounts=linked_account_ids,
        ),
    )


def try_trigger_valuation(user_account_id: int, linked_account_ids: list[int] | None = None) -> None:
    try:
        trigger_valuation(user_account_id, linked_account_ids)
    except Exception as e:
        logger.warning(
            f"failed to trigger valuation for account_id={user_account_id} linked_account_ids={linked_account_ids}: {e}"
        )
