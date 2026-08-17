from datetime import datetime, UTC

from ceo_radar.timeframe import LOOKBACK_YEARS, allowed_years, is_year_allowed, window_start_date


def test_allowed_years_includes_current_and_previous():
    now = datetime(2026, 7, 27, tzinfo=UTC)
    assert allowed_years(now) == {2026, 2025}
    assert LOOKBACK_YEARS == 1


def test_is_year_allowed():
    now = datetime(2026, 7, 27, tzinfo=UTC)
    assert is_year_allowed(2026, now) is True
    assert is_year_allowed(2025, now) is True
    assert is_year_allowed(2024, now) is False
    assert is_year_allowed(None, now) is False


def test_window_start_date():
    now = datetime(2026, 7, 27, tzinfo=UTC)
    assert window_start_date(now).isoformat() == "2025-01-01"
