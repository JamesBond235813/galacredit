"""risktable Ghana v3 异步风控接口适配器。"""

from datetime import datetime
from typing import Any, Optional

import httpx

from app.core.config import settings
from app.services.sms_filter import filter_sms_messages


class GhanaRiskClient:
    """调用 Ghana 风控平台提交和查询接口。"""

    provider = "RISKTABLE_GHANA_V3"

    def is_configured(self) -> bool:
        """判断外部风控接口是否具备调用条件。

        :return: 已启用且配置完整时返回 True
        """
        return bool(
            settings.GHANA_RISK_ENABLED
            and settings.GHANA_RISK_API_BASE_URL
            and settings.GHANA_RISK_CUSTOMER_ID
            and settings.GHANA_RISK_CUSTOMER_SECRET_KEY
        )

    def _url(self, path: str) -> str:
        """拼接接口地址。

        :param path: 接口路径
        :return: 完整 URL
        """
        return f"{settings.GHANA_RISK_API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"

    async def submit_task(
        self,
        *,
        request_id: str,
        apply_id: str,
        apply_time: datetime,
        sms_list: list[dict[str, Any]],
        app_list: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """提交异步 Ghana 风控任务。

        :param request_id: 商户侧唯一请求号
        :param apply_id: 订单号
        :param apply_time: 申请时间
        :param sms_list: 已完成90天及关键词过滤的短信
        :param app_list: 应用摘要列表
        :return: 统一状态、任务号和脱敏响应
        """
        if not self.is_configured() or not settings.GHANA_RISK_CALLBACK_URL:
            return {"status": "SKIPPED", "reason": "Provider is not configured", "response": {}}
        # 外部客户端不应成为短信过滤边界；即使上游调用方漏做过滤，这里也再次执行
        # 90 天窗口和关键词正则，确保发送给第三方的内容符合最小化采集政策。
        filtered_sms = filter_sms_messages(sms_list)
        payload = {
            "customer_id": settings.GHANA_RISK_CUSTOMER_ID,
            "request_id": request_id,
            "customer_secret_key": settings.GHANA_RISK_CUSTOMER_SECRET_KEY,
            "callback_url": settings.GHANA_RISK_CALLBACK_URL,
            "risk_data": {
                "applyId": apply_id,
                "applyTime": apply_time.strftime("%Y-%m-%d %H:%M:%S"),
                "smsList": [
                    {
                        "address": str(item.get("address") or item.get("sender") or "")[:120],
                        "body": str(item.get("body") or "")[:2000],
                        "type": int(item.get("type") or 1),
                        "time": str(item.get("time") or "")[:32],
                        "read": int(item.get("read") or 0),
                    }
                    for item in filtered_sms
                ],
                "appList": [
                    {
                        "appName": str(item.get("name") or item.get("appName") or "")[:120],
                        "packageName": str(item.get("package") or item.get("packageName") or "")[:120],
                        "firstInstallTime": str(item.get("firstInstallTime") or "")[:32],
                        "lastUpdateTime": str(item.get("lastUpdateTime") or "")[:32],
                    }
                    for item in app_list
                ],
            },
        }
        try:
            async with httpx.AsyncClient(timeout=settings.GHANA_RISK_TIMEOUT_SECONDS) as client:
                response = await client.post(self._url("gh_submit_data_v3"), json=payload)
            body = response.json()
            if response.status_code != 200 or body.get("code") != 200:
                return {"status": "FAILED", "reason": body.get("msg") or f"HTTP {response.status_code}", "response": {"code": body.get("code"), "msg": body.get("msg")}}
            data = body.get("data") or {}
            return {"status": "SUCCESS", "task_number": data.get("task_number"), "reason": data.get("message"), "response": {"code": body.get("code"), "data": data}}
        except (httpx.HTTPError, ValueError) as exc:
            return {"status": "FAILED", "reason": str(exc)[:500], "response": {}}

    async def query_task(self, *, task_number: str) -> dict[str, Any]:
        """查询 Ghana 风控任务结果。

        :param task_number: 创建任务返回的任务号
        :return: 统一状态、评分和任务状态
        """
        if not self.is_configured():
            return {"status": "SKIPPED", "reason": "Provider is not configured", "response": {}}
        payload = {
            "customer_id": settings.GHANA_RISK_CUSTOMER_ID,
            "customer_secret_key": settings.GHANA_RISK_CUSTOMER_SECRET_KEY,
            "task_number": task_number,
        }
        try:
            async with httpx.AsyncClient(timeout=settings.GHANA_RISK_TIMEOUT_SECONDS) as client:
                response = await client.post(self._url("gh_query_data_v3"), json=payload)
            body = response.json()
            if response.status_code != 200 or body.get("code") != 200:
                return {"status": "FAILED", "reason": body.get("msg") or f"HTTP {response.status_code}", "response": {"code": body.get("code"), "msg": body.get("msg")}}
            data = body.get("data") or {}
            return {"status": "SUCCESS", "task_status": data.get("task_status"), "score": data.get("task_score_v2") or data.get("task_score"), "reason": data.get("message"), "response": {"code": body.get("code"), "data": data}}
        except (httpx.HTTPError, ValueError) as exc:
            return {"status": "FAILED", "reason": str(exc)[:500], "response": {}}


ghana_risk_client = GhanaRiskClient()
