from datetime import UTC, datetime

from ceo_radar.formatters import format_person_display, format_role_label, format_timing
from ceo_radar.models import Article, Event


def test_person_fallback():
    assert format_person_display({"person": "Diego Salazar"}) == "Diego Salazar"
    assert format_person_display({}) == "Persona no identificada"


def test_role_label():
    assert format_role_label("ceo") == "CEO"
    assert format_role_label(None) == "Posición no identificada"


def test_timing_relative_months():
    article = Article(
        id="a",
        source="test",
        url="https://example.com",
        title="t",
        published_at=datetime(2026, 3, 12),
    )
    event = Event(
        id="e",
        articles=[article],
        first_seen=datetime(2026, 3, 12),
        last_seen=datetime(2026, 3, 12),
        entities={},
    )
    label = format_timing(event, now=datetime(2026, 7, 27, tzinfo=UTC))
    assert label.startswith("12 mar 2026")
    assert "hace" in label
