from datetime import date, datetime
from types import SimpleNamespace

import pytest

from app.api.endpoints import admin


class _FakeScalarRows:
    def __init__(self, rows):
        self._rows = rows

    def unique(self):
        return self

    def scalars(self):
        return self

    def all(self):
        return self._rows


class _FakeDb:
    def __init__(self, users):
        self._users = users
        self.user_stmt_sql = ""
        self.total_stmt_sql = ""

    async def scalar(self, stmt):
        self.total_stmt_sql = str(stmt)
        return len(self._users)

    async def execute(self, stmt):
        self.user_stmt_sql = str(stmt)
        return _FakeScalarRows(self._users)


@pytest.mark.asyncio
async def test_get_users_should_build_first_deal_time_filter_for_business_consultant(monkeypatch):
    monkeypatch.setattr(admin, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(admin, "_is_business_consultant", lambda *_args, **_kwargs: True)

    user = SimpleNamespace(
        id=1,
        phone="13800000001",
        name="测试用户",
        id_card_num="330301199901011111",
        face_auth_status="PASS",
        approved_limit=1000,
        created_at=datetime(2026, 4, 1, 10, 0, 0),
        last_login_at=None,
        application_submitted_at=None,
        source_channel=SimpleNamespace(channel_name="ch1", sales_name="s1"),
        channel_bound_at=None,
        last_channel_visit_at=None,
        loans=[
            SimpleNamespace(
                id=10,
                user_id=1,
                status="DISBURSED",
                disbursed_at=datetime(2026, 4, 10, 10, 0, 0),
                product_total_price=1888,
                owner=SimpleNamespace(loans=[]),
            ),
        ],
    )
    db = _FakeDb([user])
    current_admin = SimpleNamespace(id=9, roles='["BUSINESS_CONSULTANT"]')

    result = await admin.get_users(
        keyword=None,
        deal_time_start=date(2026, 4, 1),
        deal_time_end=date(2026, 4, 30),
        skip=0,
        limit=20,
        db=db,
        current_admin=current_admin,
    )

    assert result["total"] == 1
    assert len(result["items"]) == 1
    assert result["items"][0]["first_disbursed_at"] == datetime(2026, 4, 10, 10, 0, 0)
    assert "min(loans.disbursed_at)" in db.user_stmt_sql
    assert "first_disbursed_at" in db.user_stmt_sql
    assert "channels.admin_user_id" in db.user_stmt_sql
