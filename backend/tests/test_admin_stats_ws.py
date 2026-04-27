from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import admin as admin_endpoints
from app.core.database import get_async_db


def test_admin_stats_ws_should_push_stats_payload(monkeypatch):
    async def _override_db():
        yield object()

    async def _fake_get_ws_admin_by_token(_db, token):
        if token == "ok-token":
            return SimpleNamespace(id=1, roles='["ADMIN"]', permissions='["overview"]')
        return None

    async def _fake_get_stats(*, db, current_admin):
        return {
            "reviewing_loans": 3,
            "withdrawing_loans": 2,
            "due_today_users": 1,
            "repay_attempt_total": 4,
            "total_users": 10,
            "today_new_users": 0,
            "today_applications": 0,
            "approved_loans": 0,
            "disbursed_loans": 0,
            "due_today_loans": 0,
            "overdue_loans": 0,
            "today_disbursed_amount": 0.0,
            "today_reminders": 0,
            "today_collections": 0,
        }

    monkeypatch.setattr(admin_endpoints, "_get_ws_admin_by_token", _fake_get_ws_admin_by_token)
    monkeypatch.setattr(admin_endpoints, "get_stats", _fake_get_stats)
    monkeypatch.setattr(admin_endpoints, "ADMIN_STATS_WS_PUSH_SECONDS", 0.01)

    app = FastAPI()
    app.include_router(admin_endpoints.router, prefix="/api/admin")
    app.dependency_overrides[get_async_db] = _override_db

    client = TestClient(app)
    with client.websocket_connect("/api/admin/ws/stats?token=ok-token") as websocket:
        payload = websocket.receive_json()
        assert payload["type"] == "admin_stats"
        assert payload["data"]["reviewing_loans"] == 3
        assert payload["data"]["withdrawing_loans"] == 2
