from finbot.core.errors import FinbotError


class SnapshotError(FinbotError):
    pass


class InconsistentSnapshotData(SnapshotError):
    pass
