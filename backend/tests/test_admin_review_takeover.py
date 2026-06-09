from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import admin_service
from app.services.admin_permissions import resolve_permissions_from_roles


class _FakeScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _FakeDb:
    def __init__(self, values):
        self._values = list(values)
        self.committed = False

    async def execute(self, _stmt):
        return _FakeScalarResult(self._values.pop(0))

    async def commit(self):
        self.committed = True


def _admin(admin_id, username, roles):
    return SimpleNamespace(
        id=admin_id,
        username=username,
        roles=f'["{roles}"]',
        permissions=None,
    )


@pytest.mark.asyncio
async def test_review_admin_can_take_over_reviewing_loan_to_self(monkeypatch):
    events = []

    async def _fake_log_user_event_async(_db, **kwargs):
        events.append(kwargs)

    monkeypatch.setattr(admin_service, "log_user_event_async", _fake_log_user_event_async)

    current_admin = _admin(8, "review08", "REVIEW")
    assignee = _admin(8, "review08", "REVIEW")
    loan = SimpleNamespace(id=21, status="REVIEWING", review_admin_id=3, owner=SimpleNamespace(id=101))
    db = _FakeDb([loan, assignee])

    result = await admin_service._assign_loan(
        db,
        current_admin,
        loan_id=21,
        req=SimpleNamespace(stage="review", admin_id=8),
    )

    assert db.committed is True
    assert loan.review_admin_id == 8
    assert result["assignee_id"] == 8
    assert events[0]["title"] == "审核员转入自己"


@pytest.mark.asyncio
async def test_review_admin_cannot_assign_review_loan_to_other_admin():
    current_admin = _admin(8, "review08", "REVIEW")
    db = _FakeDb([])

    with pytest.raises(HTTPException) as exc_info:
        await admin_service._assign_loan(
            db,
            current_admin,
            loan_id=21,
            req=SimpleNamespace(stage="review", admin_id=9),
        )

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_review_admin_cannot_take_over_non_reviewing_loan():
    current_admin = _admin(8, "review08", "REVIEW")
    loan = SimpleNamespace(id=21, status="APPROVED", review_admin_id=3, owner=SimpleNamespace(id=101))
    db = _FakeDb([loan])

    with pytest.raises(HTTPException) as exc_info:
        await admin_service._assign_loan(
            db,
            current_admin,
            loan_id=21,
            req=SimpleNamespace(stage="review", admin_id=8),
        )

    assert exc_info.value.status_code == 400


def test_review_role_should_include_takeover_permission():
    assert "loan-review-takeover" in resolve_permissions_from_roles(["REVIEW"])
