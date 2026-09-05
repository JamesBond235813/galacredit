import asyncio
import re
from datetime import datetime
from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.endpoints import loan
from app.core.exceptions import BizException, biz_exception_handler
from app.api.deps import get_current_user_async


def test_generate_order_no_should_match_required_pattern():
    order_no = loan.generate_order_no(datetime(2026, 4, 29, 12, 30, 45, 123000))
    assert re.fullmatch(r"20260429123045123[A-Z0-9]{4}", order_no)


def test_send_order_sms_code_should_return_cooldown(monkeypatch):
    app = FastAPI()
    app.add_exception_handler(BizException, biz_exception_handler)
    app.include_router(loan.router, prefix="/api/loan")
    app.dependency_overrides[get_current_user_async] = lambda: SimpleNamespace(id=9527)

    class _FakeDbSession:
        async def execute(self, *_args, **_kwargs):
            return SimpleNamespace(scalar_one=lambda: SimpleNamespace(phone="13800000000", id=9527))

    async def _fake_get_async_db():
        yield _FakeDbSession()

    app.dependency_overrides[loan.get_async_db] = _fake_get_async_db

    class _FakeSmsService:
        async def send_code(self, phone: str, biz_type: str):
            assert phone == "13800000000"
            assert biz_type == "ORDER"
            return True, 60, "验证码发送成功"

        async def verify_code(self, phone: str, biz_type: str, code: str):
            return True

    monkeypatch.setattr(loan, "sms_service", _FakeSmsService())
    client = TestClient(app)
    resp = client.post("/api/loan/order-sms-code")
    assert resp.status_code == 200
    assert resp.json()["cooldown_seconds"] == 60


def test_send_order_sms_code_should_return_429_when_frequent(monkeypatch):
    app = FastAPI()
    app.add_exception_handler(BizException, biz_exception_handler)
    app.include_router(loan.router, prefix="/api/loan")
    app.dependency_overrides[get_current_user_async] = lambda: SimpleNamespace(id=9527)

    class _FakeDbSession:
        async def execute(self, *_args, **_kwargs):
            return SimpleNamespace(scalar_one=lambda: SimpleNamespace(phone="13800000000", id=9527))

    async def _fake_get_async_db():
        yield _FakeDbSession()

    app.dependency_overrides[loan.get_async_db] = _fake_get_async_db

    class _FakeSmsService:
        async def send_code(self, phone: str, biz_type: str):
            return False, 59, "发送过于频繁，请59秒后重试"

        async def verify_code(self, phone: str, biz_type: str, code: str):
            return True

    monkeypatch.setattr(loan, "sms_service", _FakeSmsService())
    client = TestClient(app)
    resp = client.post("/api/loan/order-sms-code")
    assert resp.status_code == 200
    assert resp.json()["code"] == 429
    assert "发送过于频繁" in resp.json()["msg"]


def test_withdraw_should_reject_when_sms_code_invalid(monkeypatch):
    async def _run():
        class _ExecuteResult:
            def __init__(self, value):
                self._value = value

            def scalar_one(self):
                return self._value

            def scalar_one_or_none(self):
                return self._value

            def scalars(self):
                return self

            def first(self):
                return self._value

        class _FakeDb:
            async def execute(self, statement):
                text_stmt = str(statement)
                if "FROM users" in text_stmt:
                    return _ExecuteResult(SimpleNamespace(id=9527, phone="13800000000", id_card_num=None, approved_limit=2000))
                return _ExecuteResult(None)

        async def _fake_get_or_create_latest_loan(_db, _user_id):
            return SimpleNamespace(status="APPROVED")

        class _FakeSmsService:
            async def verify_code(self, phone: str, biz_type: str, code: str):
                return False

        monkeypatch.setattr(loan, "get_or_create_latest_loan", _fake_get_or_create_latest_loan)
        monkeypatch.setattr(loan, "sms_service", _FakeSmsService())

        try:
            await loan.withdraw(
                req=SimpleNamespace(product_id=1, sms_code="123456", extension_source_loan_id=None, use_discount=False, contract_signature_id=1),
                current_user=SimpleNamespace(id=9527),
                db=_FakeDb(),
            )
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 200
            assert exc.code == 400
            assert "验证码" in str(exc.detail)

    asyncio.run(_run())
