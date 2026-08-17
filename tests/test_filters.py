from datetime import datetime, UTC

from ceo_radar.filters import FilterState, apply_filters
from ceo_radar.models import Article, Event


def _event(
    event_id: str,
    *,
    role: str | None = None,
    sector: str | None = None,
    first_seen: datetime,
) -> Event:
    entities = {}
    if role:
        entities["role"] = role
    if sector:
        entities["sector"] = sector
    article = Article(
        id=f"a-{event_id}",
        source="test",
        url=f"https://example.com/{event_id}",
        title="Titular de prueba",
        published_at=first_seen,
    )
    return Event(
        id=event_id,
        articles=[article],
        first_seen=first_seen,
        last_seen=first_seen,
        entities=entities,
    )


NOW = datetime(2026, 7, 27, tzinfo=UTC)

EVENTS = [
    _event("ceo-const", role="ceo", sector="construccion", first_seen=datetime(2026, 7, 1)),
    _event("com-fin", role="gerente comercial", sector="finanzas", first_seen=datetime(2026, 6, 1)),
    _event("dir-old", role="directorio", sector="construccion", first_seen=datetime(2025, 3, 1)),
    _event("other", role="director", sector="tecnologia", first_seen=datetime(2026, 7, 20)),
    _event("none", role=None, sector=None, first_seen=datetime(2026, 1, 15)),
]


def test_default_decision_and_construction():
    state = FilterState(role_group="decision", period="todo", sector="construccion")
    result = apply_filters(EVENTS, state, now=NOW)
    assert {event.id for event in result} == {"ceo-const", "dir-old"}


def test_all_roles_all_sectors():
    state = FilterState(role_group="todos", period="todo", sector="todos")
    result = apply_filters(EVENTS, state, now=NOW)
    assert [event.id for event in result] == [event.id for event in EVENTS]


def test_comercial_group_only():
    state = FilterState(role_group="comercial", period="todo", sector="todos")
    result = apply_filters(EVENTS, state, now=NOW)
    assert [event.id for event in result] == ["com-fin"]


def test_period_last_month():
    state = FilterState(role_group="todos", period="1m", sector="todos")
    result = apply_filters(EVENTS, state, now=NOW)
    assert {event.id for event in result} == {"ceo-const", "other"}


def test_period_year_2025():
    state = FilterState(role_group="todos", period="2025", sector="todos")
    result = apply_filters(EVENTS, state, now=NOW)
    assert [event.id for event in result] == ["dir-old"]


def test_unclassified_sector():
    state = FilterState(role_group="todos", period="todo", sector="sin_clasificar")
    result = apply_filters(EVENTS, state, now=NOW)
    assert [event.id for event in result] == ["none"]
