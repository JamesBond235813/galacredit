from datetime import datetime
from types import SimpleNamespace

import pytest

from app.services.admin_service import _get_monitoring_summary, _resolve_kyc_review_flags


class _FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class _FakeDb:
    def __init__(self):
        self.calls = []
        self.values = [6, 8, 5, 7, 3, 1, 2, 4]

    async def scalar(self, stmt):
        text = str(stmt)
        self.calls.append(text)
        return self.values.pop(0)


@pytest.mark.asyncio
async def test_monitoring_summary_should_collect_jobs_and_counts(monkeypatch):
    """运营监控汇总应返回任务与核心计数。

    :return: 无返回值
    """
    monkeypatch.setattr(
        "app.services.admin_service.scheduler",
        SimpleNamespace(
            get_jobs=lambda: [
                SimpleNamespace(id="job-a", next_run_time=datetime(2026, 8, 20, 1, 0, 0), trigger="cron"),
                SimpleNamespace(id="job-b", next_run_time=None, trigger="interval"),
            ]
        ),
    )
    monkeypatch.setattr(
        "app.services.admin_service.get_today_range",
        lambda: (datetime(2026, 8, 20, 0, 0, 0), datetime(2026, 8, 21, 0, 0, 0)),
    )

    db = _FakeDb()
    current_admin = SimpleNamespace(id=1, username="root", roles='["ADMIN"]')

    summary = await _get_monitoring_summary(db, current_admin)

    assert summary["momo_pending_count"] == 3
    assert summary["momo_failed_count"] == 1
    assert summary["active_compliance_rule_count"] == 2
    assert summary["overdue_loan_count"] == 4
    assert len(summary["scheduled_jobs"]) == 2
    assert summary["scheduled_jobs"][0]["job_id"] == "job-a"


def test_resolve_kyc_review_flags_should_accept_multiple_pass_statuses():
    """KYC 复核标签应兼容多种已通过状态值。

    :return: 无返回值
    """
    user = SimpleNamespace(
        real_name_status="AUTHED",
        face_auth_status="PASSED",
        id_card_num="440100199001010011",
        location_risk_blocked=False,
        blacklist_hit=False,
        risk_list_hit=False,
    )

    assert _resolve_kyc_review_flags(user) == []
