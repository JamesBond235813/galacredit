import asyncio
from datetime import datetime
from types import SimpleNamespace

from fastapi import HTTPException

from app.api.endpoints import admin


def test_disburse_should_use_expiry_date_gt_today_and_return_new_message():
    async def _run():
        loan = SimpleNamespace(
            id=1,
            status="WITHDRAWING",
            owner=SimpleNamespace(id=11, phone="13800000000"),
            ecard_face_value=1000.0,
            credit_limit=1000.0,
            product_term_days=14,
            term_days=14,
        )

        class _ExecuteResult:
            def __init__(self, value):
                self._value = value

            def scalar_one_or_none(self):
                return self._value

            def scalars(self):
                return self

            def first(self):
                return self._value

        class _FakeDb:
            def __init__(self):
                self.calls = 0
                self.last_stmt = None

            async def execute(self, stmt):
                self.calls += 1
                self.last_stmt = stmt
                if self.calls == 1:
                    return _ExecuteResult(loan)
                return _ExecuteResult(None)

        db = _FakeDb()
        current_admin = SimpleNamespace(username="admin", roles='["ADMIN"]', permissions=None)
        req = SimpleNamespace(term_days=14)
        try:
            await admin._disburse_loan(db, current_admin, loan_id=1, req=req)
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "卡池库存不足：未找到面额 1000.00 元且有效的京东E卡"
            stmt_sql = str(db.last_stmt)
            assert "ecard_pool.expires_at >=" in stmt_sql.lower()
            assert "ecard_pool.expires_at" in stmt_sql

    asyncio.run(_run())


def test_disburse_should_reject_even_if_today_expired_card_is_returned():
    async def _run():
        now = datetime.now()
        loan = SimpleNamespace(
            id=1,
            status="WITHDRAWING",
            owner=SimpleNamespace(id=11, phone="13800000000"),
            ecard_face_value=1000.0,
            credit_limit=1000.0,
            product_term_days=14,
            term_days=14,
        )
        today_card = SimpleNamespace(
            id=8,
            account="acc",
            password="pwd",
            face_value=1000.0,
            expires_at=datetime(now.year, now.month, now.day, 23, 59, 59),
            status="AVAILABLE",
        )

        class _ExecuteResult:
            def __init__(self, value):
                self._value = value

            def scalar_one_or_none(self):
                return self._value

            def scalars(self):
                return self

            def first(self):
                return self._value

        class _FakeDb:
            def __init__(self):
                self.calls = 0

            async def execute(self, _stmt):
                self.calls += 1
                if self.calls == 1:
                    return _ExecuteResult(loan)
                return _ExecuteResult(today_card)

        db = _FakeDb()
        current_admin = SimpleNamespace(username="admin", roles='["ADMIN"]', permissions=None)
        req = SimpleNamespace(term_days=14)
        try:
            await admin._disburse_loan(db, current_admin, loan_id=1, req=req)
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 400
            assert exc.detail == "卡池库存不足：未找到面额 1000.00 元且有效的京东E卡"

    asyncio.run(_run())
