import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.services.blacklist_service import md5_text, normalize_identity_value

logger = logging.getLogger(__name__)


@dataclass
class RiskListMatchResult:
    """风险名单撞库结果。

    :param hit: 是否命中风险名单
    :param source: 撞库来源
    :param reason: 命中或未完成原因
    :return: 风险名单撞库结果
    """

    hit: bool
    source: str
    reason: Optional[str] = None


def build_legou_risk_payload(*, phone: Optional[str], id_card_num: Optional[str]) -> dict:
    """构建乐购风险名单撞库入参。

    :param phone: 手机号明文
    :param id_card_num: 身份证号明文
    :return: 接口入参
    """
    return {
        "phoneMd5": md5_text(phone),
        "idCardMd5": md5_text(id_card_num),
    }


async def match_legou_blacklist_async(*, phone: Optional[str], id_card_num: Optional[str]) -> RiskListMatchResult:
    """调用乐购外部黑名单接口。

    :param phone: 手机号明文
    :param id_card_num: 身份证号明文
    :return: 风险名单撞库结果
    """
    phone_text = normalize_identity_value(phone)
    id_card_text = normalize_identity_value(id_card_num)
    if not phone_text and not id_card_text:
        return RiskListMatchResult(hit=False, source="LEGOU", reason="缺少手机号和身份证号")
    if not settings.RISK_LEGOU_ENABLED:
        return RiskListMatchResult(hit=False, source="LEGOU", reason="乐购风险名单接口未启用")
    if not settings.RISK_LEGOU_TOKEN:
        return RiskListMatchResult(hit=False, source="LEGOU", reason="乐购风险名单接口token未配置")

    payload = build_legou_risk_payload(phone=phone_text, id_card_num=id_card_text)
    try:
        async with httpx.AsyncClient(timeout=settings.RISK_LEGOU_TIMEOUT_SECONDS) as client:
            response = await client.post(
                settings.RISK_LEGOU_BLACKLIST_URL,
                json=payload,
                headers={"token": settings.RISK_LEGOU_TOKEN},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.warning("legou_risk_match_failed phone=%s error=%s", phone_text, exc)
        return RiskListMatchResult(hit=False, source="LEGOU", reason="乐购风险名单接口调用失败")

    if data.get("code") != 200:
        reason = data.get("errorMsg") or data.get("bizCode") or "乐购风险名单接口返回失败"
        return RiskListMatchResult(hit=False, source="LEGOU", reason=str(reason))
    if bool(data.get("result")):
        return RiskListMatchResult(hit=True, source="LEGOU", reason="命中乐购风险名单")
    return RiskListMatchResult(hit=False, source="LEGOU", reason=None)


async def refresh_user_risk_list_status(db: AsyncSession, user: User) -> RiskListMatchResult:
    """刷新用户风险名单命中状态。

    :param db: 异步数据库会话
    :param user: 用户对象
    :return: 风险名单撞库结果
    """
    if not normalize_identity_value(getattr(user, "id_card_num", None)):
        # 未完成实名前仅有手机号，先不使用外部风险名单拦截身份证上传流程。
        user.risk_list_checked_at = datetime.now()
        user.risk_list_hit = False
        user.risk_list_source = None
        user.risk_list_reason = None
        return RiskListMatchResult(hit=False, source="LEGOU", reason="未实名用户暂不执行风险名单撞库")

    result = await match_legou_blacklist_async(
        phone=getattr(user, "phone", None),
        id_card_num=getattr(user, "id_card_num", None),
    )
    user.risk_list_checked_at = datetime.now()
    user.risk_list_hit = result.hit
    user.risk_list_source = result.source if result.hit else None
    user.risk_list_reason = result.reason if result.hit else None
    return result
