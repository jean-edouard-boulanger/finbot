from sqlalchemy import desc
from finbot.model import UserAccountHistoryEntry


def find_last_user_account_history_entry(session, user_account_id):
    return (session.query(UserAccountHistoryEntry)
                   .filter_by(user_account_id=user_account_id)
                   .filter_by(available=True)
                   .order_by(desc(UserAccountHistoryEntry.effective_at))
                   .first())
