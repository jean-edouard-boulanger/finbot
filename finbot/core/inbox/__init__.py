"""In-app notifications: the inbox a user sees in the notification panel.

Distinct from `finbot.core.notifier`, which delivers outbound email and SMS. This module owns the persisted
notification list and its aggregation semantics; that one owns messages sent out of the system.
"""

from finbot.core.inbox.service import (
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_SUCCESS,
    SEVERITY_WARNING,
    STATUS_ACTIVE,
    STATUS_RESOLVED,
    RaiseResult,
    dismiss_open_notification,
    raise_notification,
    resolve_notification,
)

__all__ = [
    "SEVERITY_ERROR",
    "SEVERITY_INFO",
    "SEVERITY_SUCCESS",
    "SEVERITY_WARNING",
    "STATUS_ACTIVE",
    "STATUS_RESOLVED",
    "RaiseResult",
    "dismiss_open_notification",
    "raise_notification",
    "resolve_notification",
]
