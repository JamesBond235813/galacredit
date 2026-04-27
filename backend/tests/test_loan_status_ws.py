from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints import loan as loan_endpoints
from app.core.database import get_async_db


def test_loan_status_ws_should_push_snapshot_payload(monkeypatch):
    async def _override_db():
        yield object()

    async def _fake_get_ws_user_by_token(_db, token):
        if token == "ok-token":
            return SimpleNamespace(id=7)
        return None

    async def _fake_get_latest_loan_snapshot_async(_db, _user_id):
        return SimpleNamespace(id=9, status="REVIEWING")

    def _fake_serialize_loan_snapshot(_loan, include_ledger=False):
        return {"id": 9, "status": "REVIEWING", "include_ledger": include_ledger}

    monkeypatch.setattr(loan_endpoints, "_get_ws_user_by_token", _fake_get_ws_user_by_token)
    monkeypatch.setattr(loan_endpoints, "get_latest_loan_snapshot_async", _fake_get_latest_loan_snapshot_async)
    monkeypatch.setattr(loan_endpoints, "serialize_loan_snapshot", _fake_serialize_loan_snapshot)
    monkeypatch.setattr(loan_endpoints, "LOAN_STATUS_WS_PUSH_SECONDS", 0.01)

    app = FastAPI()
    app.include_router(loan_endpoints.router, prefix="/api/loan")
    app.dependency_overrides[get_async_db] = _override_db

    client = TestClient(app)
    with client.websocket_connect("/api/loan/ws/status?token=ok-token") as websocket:
        payload = websocket.receive_json()
        assert payload["type"] == "loan_snapshot"
        assert payload["data"]["id"] == 9
        assert payload["data"]["status"] == "REVIEWING"
        assert payload["data"]["include_ledger"] is True

