from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services import admin_service
from app.services.admin_permissions import resolve_permissions_from_roles


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class _ScalarsResult:
    def __init__(self, values):
        self._values = values

    def scalars(self):
        return self

    def all(self):
        return self._values


class _FakeDbForResolveAdvisor:
    def __init__(self, advisor):
        self._advisor = advisor

    async def execute(self, _stmt):
        return _ScalarResult(self._advisor)


class _FakeDbForListAdvisors:
    def __init__(self, admins):
        self._admins = admins

    async def execute(self, _stmt):
        return _ScalarsResult(self._admins)


@pytest.mark.asyncio
async def test_resolve_business_advisor_by_id_should_reject_non_consultant():
    db = _FakeDbForResolveAdvisor(SimpleNamespace(id=12, username="u12", roles='["REVIEW"]'))

    with pytest.raises(HTTPException) as exc_info:
        await admin_service._resolve_business_advisor_by_id(db, 12)

    assert exc_info.value.status_code == 400
    assert "业务顾问" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_business_advisors_should_return_only_consultants(monkeypatch):
    monkeypatch.setattr(admin_service, "ensure_admin_page_permission", lambda *_args, **_kwargs: None)
    db = _FakeDbForListAdvisors(
        [
            SimpleNamespace(id=9, username="superadmin", roles='["ADMIN"]'),
            SimpleNamespace(id=1, username="reviewer", roles='["REVIEW"]'),
            SimpleNamespace(id=2, username="consultantA", roles='["BUSINESS_CONSULTANT"]'),
            SimpleNamespace(id=3, username="consultantB", roles='["BUSINESS_CONSULTANT", "REVIEW"]'),
        ]
    )
    current_admin = SimpleNamespace(id=99, username="admin", roles='["ADMIN"]', permissions='["channels"]')

    result = await admin_service._get_business_advisors(db, current_admin, keyword="consultant", limit=10)

    assert [item.id for item in result] == [2, 3]
    assert [item.username for item in result] == ["consultantA", "consultantB"]


@pytest.mark.asyncio
async def test_resolve_business_advisor_by_id_should_reject_admin_only_role():
    db = _FakeDbForResolveAdvisor(SimpleNamespace(id=100, username="root", roles='["ADMIN"]'))

    with pytest.raises(HTTPException) as exc_info:
        await admin_service._resolve_business_advisor_by_id(db, 100)

    assert exc_info.value.status_code == 400
    assert "业务顾问" in str(exc_info.value.detail)


def test_business_consultant_role_should_map_to_users_page_only():
    permissions = resolve_permissions_from_roles(["BUSINESS_CONSULTANT"])

    assert permissions == ["users"]
