from types import SimpleNamespace

import pytest

from app.services.admin_service import _get_disbursement_failures


class _EmptyResult:
    def all(self):
        return []


class _EmptyDb:
    async def scalar(self, _statement):
        return 0

    async def execute(self, _statement):
        return _EmptyResult()


@pytest.mark.asyncio
async def test_disbursement_failure_queue_returns_deduplicated_empty_shape():
    """失败队列无数据时仍返回稳定的分页和汇总结构。"""
    result = await _get_disbursement_failures(
        _EmptyDb(),
        SimpleNamespace(id=1, roles='["ADMIN"]', permissions=None),
        keyword=None,
        skip=0,
        limit=20,
    )

    assert result == {
        "total": 0,
        "page": 1,
        "size": 20,
        "summary": {"failed_count": 0, "failed_amount": 0.0},
        "items": [],
    }
