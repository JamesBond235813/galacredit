from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.admin_service import _resolve_single_risk_subject


class _FakeScalarResult:
    """模拟SQLAlchemy标量结果。

    :param items: 结果列表
    :return: 无返回值
    """

    def __init__(self, items):
        self.items = items

    def scalars(self):
        return self

    def all(self):
        return self.items


class _FakeDb:
    """模拟异步数据库会话。

    :param items: 用户结果列表
    :return: 无返回值
    """

    def __init__(self, items):
        self.items = items

    async def execute(self, _stmt):
        return _FakeScalarResult(self.items)


@pytest.mark.asyncio
async def test_single_risk_subject_rejects_empty_input():
    """单查不填写任何信息时应提示补充查询条件。

    :return: 无返回值
    """
    with pytest.raises(HTTPException) as exc:
        await _resolve_single_risk_subject(_FakeDb([]), name="", id_card="", phone="")

    assert exc.value.status_code == 400
    assert "至少填写" in exc.value.detail


@pytest.mark.asyncio
async def test_single_risk_subject_fills_from_matched_user():
    """单查匹配唯一用户时应自动补齐缺失三要素。

    :return: 无返回值
    """
    user = SimpleNamespace(id=7, name="张三", id_card_num="440100199001010011", phone="13900000000")

    resolved = await _resolve_single_risk_subject(_FakeDb([user]), name="张三", id_card="", phone="")

    assert resolved == ("张三", "440100199001010011", "13900000000", 7)


@pytest.mark.asyncio
async def test_single_risk_subject_allows_complete_external_subject():
    """系统内未匹配但三要素完整时应允许外部单查。

    :return: 无返回值
    """
    resolved = await _resolve_single_risk_subject(
        _FakeDb([]),
        name="李四",
        id_card="440100199001010022",
        phone="13800000000",
    )

    assert resolved == ("李四", "440100199001010022", "13800000000", None)
