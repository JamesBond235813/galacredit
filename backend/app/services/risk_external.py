from dataclasses import dataclass
from typing import Any, Optional

from app.services.risk_scoring import RuleScore, calculate_rule_scores


@dataclass(frozen=True)
class ExternalRiskResult:
    """外部风险服务的统一结果。"""

    provider: str
    status: str
    score: Optional[float]
    reason: str
    raw: dict[str, Any]


class GhanaRiskProvider:
    """加纳外部数据供应商适配器接口，默认安全降级。"""

    provider = "UNCONFIGURED"

    async def check(self, *, user_reference: str, check_type: str) -> ExternalRiskResult:
        """执行外部查询；未配置供应商时返回可审计的跳过结果。

        :param user_reference: 脱敏用户参考号
        :param check_type: 查询类型
        :return: 统一外部风险结果
        """
        return ExternalRiskResult(self.provider, "SKIPPED", None, "Provider is not configured", {"check_type": check_type})


def combine_external_score(base: RuleScore, external: Optional[ExternalRiskResult]) -> RuleScore:
    """把已授权的外部评分安全合并到规则结果，跳过或失败时保持内部结果。

    :param base: 内部规则评分
    :param external: 外部评分结果
    :return: 合并后的评分
    """
    if external is None or external.status != "SUCCESS" or external.score is None:
        return base
    score = max(0.0, min(100.0, (base.fraud_score * 0.7) + (float(external.score) * 0.3)))
    decision = "BLOCK" if score >= 80 else "REFER" if score >= 35 else base.decision
    return RuleScore(round(score, 2), base.credit_score, decision, base.recommended_limit, base.reasons + ("EXTERNAL_SCORE_USED",))
