from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_rule import ComplianceRule
from app.core.exceptions import BizException

CASH_LOAN_FEE_COMPONENT_KEYS = (
    "system_service_fee_rate",
    "control_fee_rate",
    "channel_fee_rate",
    "interest_rate",
)


def normalize_cash_loan_fee_components(value: Any) -> Dict[str, float]:
    """规范化现金贷四项上扣费率。

    :param value: 后台提交的费用分项映射
    :return: 四项费率映射
    """
    source = value if isinstance(value, dict) else {}
    result = {}
    for key in CASH_LOAN_FEE_COMPONENT_KEYS:
        try:
            rate = float(source.get(key, 0) or 0)
        except (TypeError, ValueError) as exc:
            raise BizException("现金贷费用分项必须为数字费率") from exc
        if rate < 0 or rate > 1:
            raise BizException("现金贷费用分项费率必须在0%至100%之间")
        result[key] = round(rate, 6)
    return result


def validate_cash_loan_fee_components(upfront_fee_rate: Any, fee_components: Any) -> Dict[str, float]:
    """校验现金贷四项费率之和等于总上扣费率。

    :param upfront_fee_rate: 总上扣费率
    :param fee_components: 四项费用费率
    :return: 规范化后的四项费率
    """
    normalized = normalize_cash_loan_fee_components(fee_components)
    total = round(sum(normalized.values()), 6)
    target = round(float(upfront_fee_rate or 0), 6)
    if abs(total - target) > 0.000001:
        raise BizException("系统服务费、封控费用、通道费和利率之和必须等于上扣费用率")
    return normalized


def calculate_effective_apr(nominal_amount: Any, upfront_fee_rate: Any, repayment_due_day: Any) -> float:
    """按实际到账金额折算短期贷款年化费率。

    :param nominal_amount: 名义借款金额
    :param upfront_fee_rate: 上扣费用率
    :param repayment_due_day: 放款后到期天数
    :return: 折算年化费率
    """
    nominal = max(float(nominal_amount or 0), 0)
    fee_rate = max(float(upfront_fee_rate or 0), 0)
    due_day = max(int(repayment_due_day or 1), 1)
    disbursed = nominal * max(1 - fee_rate, 0)
    if nominal <= 0 or disbursed <= 0:
        return 0
    fee_amount = nominal * fee_rate
    return round((fee_amount / disbursed) * (365 / due_day), 6)


async def get_active_compliance_rule_async(db: AsyncSession, now: Optional[datetime] = None) -> Optional[ComplianceRule]:
    """读取当前生效的最新合规规则。

    :param db: 异步数据库会话
    :param now: 校验时间
    :return: 生效规则，无配置时返回 None
    """
    current = now or datetime.now()
    return (
        await db.execute(
            select(ComplianceRule)
            .where(ComplianceRule.is_active.is_(True), ComplianceRule.effective_at <= current)
            .order_by(ComplianceRule.effective_at.desc(), ComplianceRule.id.desc())
        )
    ).scalars().first()


async def validate_cash_loan_compliance_async(
    db: AsyncSession,
    *,
    nominal_amount: Any,
    upfront_fee_rate: Any,
    repayment_due_day: Any,
    daily_overdue_fee: Any,
    term_days: Any = None,
    installment_count: Any = None,
    fee_components: Any = None,
) -> Dict[str, float]:
    """按后台生效规则校验现金贷产品参数。

    :param db: 异步数据库会话
    :param nominal_amount: 名义借款金额
    :param upfront_fee_rate: 上扣费用率
    :param repayment_due_day: 到期日天数
    :param daily_overdue_fee: 每日逾期费用
    :return: 合规计算结果
    """
    rule = await get_active_compliance_rule_async(db)
    normalized_components = validate_cash_loan_fee_components(upfront_fee_rate, fee_components)
    effective_apr = calculate_effective_apr(nominal_amount, upfront_fee_rate, repayment_due_day)
    actual_disbursement_rate = max(1 - float(upfront_fee_rate or 0), 0)
    result = {
        "effective_apr": effective_apr,
        "actual_disbursement_rate": actual_disbursement_rate,
        "rule_id": float(rule.id) if rule else 0,
        "fee_components": normalized_components,
    }
    if not rule:
        return result
    if rule.max_upfront_fee_rate is not None and float(upfront_fee_rate or 0) > rule.max_upfront_fee_rate:
        raise BizException("产品上扣费用率超过当前合规上限")
    if rule.max_effective_apr is not None and effective_apr > rule.max_effective_apr:
        raise BizException("产品折算年化费率超过当前合规上限")
    if rule.max_daily_overdue_fee is not None and float(daily_overdue_fee or 0) > rule.max_daily_overdue_fee:
        raise BizException("产品每日逾期费超过当前合规上限")
    if rule.min_actual_disbursement_rate is not None and actual_disbursement_rate < rule.min_actual_disbursement_rate:
        raise BizException("产品实际到账比例低于当前合规下限")
    if rule.max_term_days is not None and int(term_days or repayment_due_day or 0) > rule.max_term_days:
        raise BizException("产品期限超过当前合规上限")
    if rule.max_installment_count is not None and int(installment_count or 1) > rule.max_installment_count:
        raise BizException("产品分期期数超过当前合规上限")
    return result


def serialize_compliance_rule(rule: Optional[ComplianceRule]) -> Optional[dict]:
    """序列化合规规则。

    :param rule: 合规规则
    :return: 规则字典
    """
    if not rule:
        return None
    return {
        "id": rule.id,
        "rule_name": rule.rule_name,
        "max_upfront_fee_rate": rule.max_upfront_fee_rate,
        "max_effective_apr": rule.max_effective_apr,
        "max_daily_overdue_fee": rule.max_daily_overdue_fee,
        "min_actual_disbursement_rate": rule.min_actual_disbursement_rate,
        "max_term_days": rule.max_term_days,
        "max_installment_count": rule.max_installment_count,
        "is_active": rule.is_active,
        "effective_at": rule.effective_at,
        "note": rule.note,
        "created_by": rule.created_by,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }
