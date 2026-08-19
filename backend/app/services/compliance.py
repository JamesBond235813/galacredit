from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.compliance_rule import ComplianceRule


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
    effective_apr = calculate_effective_apr(nominal_amount, upfront_fee_rate, repayment_due_day)
    result = {"effective_apr": effective_apr, "rule_id": float(rule.id) if rule else 0}
    if not rule:
        return result
    if rule.max_upfront_fee_rate is not None and float(upfront_fee_rate or 0) > rule.max_upfront_fee_rate:
        raise HTTPException(status_code=400, detail="产品上扣费用率超过当前合规上限")
    if rule.max_effective_apr is not None and effective_apr > rule.max_effective_apr:
        raise HTTPException(status_code=400, detail="产品折算年化费率超过当前合规上限")
    if rule.max_daily_overdue_fee is not None and float(daily_overdue_fee or 0) > rule.max_daily_overdue_fee:
        raise HTTPException(status_code=400, detail="产品每日逾期费超过当前合规上限")
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
        "is_active": rule.is_active,
        "effective_at": rule.effective_at,
        "note": rule.note,
        "created_by": rule.created_by,
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
    }
