import json
import base64
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.core.config import settings

from app.models.momo_transaction import MomoTransaction


@dataclass
class MomoTransferResult:
    """MoMo 转账结果。"""

    success: bool
    reference: str
    provider: str = "mock"
    message: str = ""


class MomoProvider:
    """MoMo 支付供应商抽象，后续只替换实现，不改放款和还款业务。"""

    async def disburse(self, phone: str, amount: float, loan_id: int) -> MomoTransferResult:
        """向借款人发起放款。

        :param phone: 借款人 MoMo 手机号
        :param amount: 实际到账金额
        :param loan_id: 贷款订单号
        :return: 转账结果
        """
        raise NotImplementedError

    async def collect(self, phone: str, amount: float, loan_id: int) -> MomoTransferResult:
        """创建还款收款请求。

        :param phone: 借款人 MoMo 手机号
        :param amount: 本次还款金额
        :param loan_id: 贷款订单号
        :return: 收款结果
        """
        raise NotImplementedError


class MockMomoProvider(MomoProvider):
    """本地开发用 MoMo 模拟实现，不连接真实资金渠道。"""

    async def disburse(self, phone: str, amount: float, loan_id: int) -> MomoTransferResult:
        return MomoTransferResult(True, f"MOCK-D-{loan_id}-{uuid4().hex[:8]}", message="模拟放款成功")

    async def collect(self, phone: str, amount: float, loan_id: int) -> MomoTransferResult:
        return MomoTransferResult(True, f"MOCK-R-{loan_id}-{uuid4().hex[:8]}", message="模拟收款成功")


class HubtelMomoProvider(MomoProvider):
    """Hubtel Checkout 收款实现。"""

    def _headers(self) -> Dict[str, str]:
        """构造 Hubtel Basic 认证请求头。"""
        token = base64.b64encode(f"{settings.HUBTEL_API_ID}:{settings.HUBTEL_API_KEY}".encode()).decode()
        return {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    async def disburse(self, phone: str, amount: float, loan_id: int) -> MomoTransferResult:
        """Hubtel 不提供本接口所需的放款能力，交由上游放款渠道处理。"""
        return MomoTransferResult(False, "", provider="hubtel", message="Hubtel暂不支持放款")

    async def collect(self, phone: str, amount: float, loan_id: int) -> MomoTransferResult:
        """创建 Hubtel 收款 Checkout。"""
        payload = {
            "totalAmount": round(float(amount), 2),
            "description": f"GalaCredit loan {loan_id} repayment",
            "callbackUrl": settings.HUBTEL_PAYMENT_CALLBACK_URL,
            "returnUrl": settings.HUBTEL_RETURN_URL,
            "cancellationUrl": settings.HUBTEL_CANCELLATION_URL,
            "clientReference": f"REPAYMENT:{loan_id}:{uuid4().hex[:12]}",
            "paymentChannels": ["momo"],
        }
        try:
            async with httpx.AsyncClient(timeout=settings.HUBTEL_HTTP_TIMEOUT_SECONDS) as client:
                response = await client.post(settings.HUBTEL_INITIATE_URL, headers=self._headers(), json=payload)
                response.raise_for_status()
                body = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return MomoTransferResult(False, "", provider="hubtel", message=f"Hubtel请求失败：{exc}")
        reference = str(body.get("checkoutId") or body.get("data", {}).get("checkoutId") or payload["clientReference"])
        success = str(body.get("responseCode", body.get("code", "200"))) in {"200", "0", "00"}
        return MomoTransferResult(success, reference, provider="hubtel", message=str(body.get("message", "")))


momo_provider: MomoProvider = HubtelMomoProvider() if settings.HUBTEL_ENABLED else MockMomoProvider()


async def create_or_get_momo_transaction_async(
    db: AsyncSession,
    *,
    loan_id: int,
    user_id: int,
    transaction_type: str,
    phone: str,
    amount: float,
    idempotency_key: str,
    provider: str = "mock",
    request_payload: Optional[dict] = None,
    related_transaction_id: Optional[int] = None,
) -> MomoTransaction:
    """创建或读取 MoMo 交易流水，确保重复请求不会生成重复资金指令。

    :param db: 异步数据库会话
    :param loan_id: 贷款订单ID
    :param user_id: 用户ID
    :param transaction_type: 交易类型
    :param phone: MoMo 手机号
    :param amount: 交易金额
    :param idempotency_key: 业务幂等键
    :return: MoMo 交易流水
    """
    transaction = (
        await db.execute(
            select(MomoTransaction).where(MomoTransaction.idempotency_key == idempotency_key)
        )
    ).scalar_one_or_none()
    if transaction:
        return transaction
    transaction = MomoTransaction(
        loan_id=loan_id,
        user_id=user_id,
        transaction_type=transaction_type,
        provider=provider,
        idempotency_key=idempotency_key,
        phone=phone,
        amount=round(float(amount or 0), 2),
        status="PENDING",
        request_payload=json.dumps(
            request_payload or {"phone": phone, "amount": amount, "loan_id": loan_id},
            ensure_ascii=False,
        ),
        related_transaction_id=related_transaction_id,
    )
    db.add(transaction)
    await db.flush()
    return transaction


def complete_momo_transaction(
    transaction: MomoTransaction,
    *,
    success: bool,
    reference: Optional[str] = None,
    provider: Optional[str] = None,
    message: str = "",
    response_payload: Optional[dict] = None,
) -> None:
    """写入 MoMo 交易的最终状态。

    :param transaction: MoMo 交易流水
    :param success: 服务商是否成功
    :param reference: 服务商流水号
    :param provider: 服务商名称
    :param message: 服务商返回信息
    :return: None
    """
    transaction.status = "SUCCESS" if success else "FAILED"
    transaction.provider_reference = reference
    transaction.provider = provider or transaction.provider
    transaction.response_payload = json.dumps(
        response_payload or {"reference": reference, "message": message},
        ensure_ascii=False,
    )
    transaction.failure_message = None if success else (message or "MoMo transaction failed")
    transaction.completed_at = datetime.now() if success else None
