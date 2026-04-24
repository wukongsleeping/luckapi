from datetime import datetime


def now() -> datetime:
    from datetime import timezone

    return datetime.now(timezone.utc)
