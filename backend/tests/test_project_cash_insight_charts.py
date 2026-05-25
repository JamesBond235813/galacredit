from datetime import datetime, timedelta
from types import SimpleNamespace

from app.services.admin_service import build_recent_insight_charts


def test_recent_insight_charts_should_count_orders_and_ecard_amounts():
    today_start = datetime(2026, 5, 19)
    loans = [
        SimpleNamespace(disbursed_at=today_start - timedelta(days=1), ecard_face_value=1000, credit_limit=1600),
        SimpleNamespace(disbursed_at=today_start - timedelta(days=1, hours=-2), ecard_face_value=500, credit_limit=800),
        SimpleNamespace(disbursed_at=today_start - timedelta(days=6), ecard_face_value=1500, credit_limit=2400),
        SimpleNamespace(disbursed_at=today_start - timedelta(days=8), ecard_face_value=2000, credit_limit=3200),
    ]

    charts = build_recent_insight_charts(loans, today_start)

    order_chart = next(item for item in charts if item["key"] == "daily_order_count")
    ecard_chart = next(item for item in charts if item["key"] == "daily_ecard_amount")
    assert len(order_chart["points"]) == 7
    assert order_chart["points"][0]["value"] == 1
    assert order_chart["points"][5]["value"] == 2
    assert order_chart["points"][6]["value"] == 0
    assert ecard_chart["points"][0]["value"] == 1500
    assert ecard_chart["points"][5]["value"] == 1500
    assert ecard_chart["points"][6]["value"] == 0
