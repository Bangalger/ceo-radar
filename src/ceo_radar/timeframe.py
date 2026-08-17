"""Ventana temporal centralizada para ingesta y filtrado."""

from __future__ import annotations

from datetime import date, datetime, UTC


LOOKBACK_YEARS = 1


def allowed_years(now: datetime | None = None) -> set[int]:
    """Retorna el set de años permitidos (actual + N anteriores)."""
    if now is None:
        now = datetime.now(UTC)
    current_year = now.year
    return {current_year - i for i in range(LOOKBACK_YEARS + 1)}


def is_year_allowed(year: int | None, now: datetime | None = None) -> bool:
    """True si el año está dentro de la ventana de ingesta."""
    if year is None:
        return False
    return year in allowed_years(now)


def window_start_date(now: datetime | None = None) -> date:
    """1 de enero del año más antiguo permitido."""
    years = allowed_years(now)
    return date(min(years), 1, 1)
