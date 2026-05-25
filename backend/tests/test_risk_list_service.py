from types import SimpleNamespace

import pytest

from app.services import risk_list_service
from app.services.risk_list_service import build_legou_risk_payload, refresh_user_risk_list_status


def test_build_legou_risk_payload_should_use_md5_values():
    """乐购风险名单接口入参应使用手机号和身份证MD5。

    :return: 无返回值
    """
    payload = build_legou_risk_payload(phone="13800000000", id_card_num="110101199001011234")

    assert payload["phoneMd5"] == "5daad257487f1b493114181a22e37eb5"
    assert payload["idCardMd5"] == "4493a36acd9549a8aa1bc7da0d30f1a6"


@pytest.mark.asyncio
async def test_refresh_user_risk_list_status_should_not_call_without_token(monkeypatch):
    """未配置token时不调用外部接口且不命中风险名单。

    :return: 无返回值
    """
    monkeypatch.setattr(risk_list_service.settings, "RISK_LEGOU_TOKEN", "")
    user = SimpleNamespace(phone="13800000000", id_card_num=None)

    result = await refresh_user_risk_list_status(SimpleNamespace(), user)

    assert result.hit is False
    assert user.risk_list_hit is False
    assert user.risk_list_source is None
    assert user.risk_list_reason is None
    assert user.risk_list_checked_at is not None


@pytest.mark.asyncio
async def test_refresh_user_risk_list_status_should_skip_unverified_phone_only_user(monkeypatch):
    """未实名用户只有手机号时，不应因外部风险名单影响身份证上传。

    :return: 无返回值
    """
    user = SimpleNamespace(phone="13800000000", id_card_num=None)

    async def _unexpected_match_legou_blacklist_async(*, phone, id_card_num):
        raise AssertionError("未实名手机号不应调用乐购风险名单")

    monkeypatch.setattr(risk_list_service, "match_legou_blacklist_async", _unexpected_match_legou_blacklist_async)

    result = await refresh_user_risk_list_status(SimpleNamespace(), user)

    assert result.hit is False
    assert result.reason == "未实名用户暂不执行风险名单撞库"
    assert user.risk_list_hit is False
    assert user.risk_list_source is None
    assert user.risk_list_reason is None
    assert user.risk_list_checked_at is not None


@pytest.mark.asyncio
async def test_refresh_user_risk_list_status_should_mark_legou_hit(monkeypatch):
    """乐购接口命中时应写入用户风险名单状态。

    :return: 无返回值
    """
    user = SimpleNamespace(phone="13800000000", id_card_num="110101199001011234")

    async def _fake_match_legou_blacklist_async(*, phone, id_card_num):
        assert phone == user.phone
        assert id_card_num == user.id_card_num
        return risk_list_service.RiskListMatchResult(hit=True, source="LEGOU", reason="命中乐购风险名单")

    monkeypatch.setattr(risk_list_service, "match_legou_blacklist_async", _fake_match_legou_blacklist_async)

    result = await refresh_user_risk_list_status(SimpleNamespace(), user)

    assert result.hit is True
    assert user.risk_list_hit is True
    assert user.risk_list_source == "LEGOU"
    assert user.risk_list_reason == "命中乐购风险名单"
