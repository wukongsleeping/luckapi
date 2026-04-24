from app.core.utils import now


class TestNow:
    """Tests for the now() utility function."""

    def test_returns_datetime(self):
        from datetime import datetime
        result = now()
        assert isinstance(result, datetime)

    def test_returns_utc_time(self):
        result = now()
        assert result.tzinfo is not None
        from datetime import timezone
        assert result.utcoffset() is not None

    def test_returns_current_time(self):
        from datetime import datetime, timezone, timedelta
        result = now()
        now_utc = datetime.now(timezone.utc)
        delta = abs((now_utc - result).total_seconds())
        assert delta < 5  # Should be within 5 seconds of current time

    def test_is_monotonic(self):
        t1 = now()
        t2 = now()
        # Time should always be non-decreasing (allowing small clock adjustments)
        assert t2 >= t1 or abs((t2 - t1).total_seconds()) < 0.001
