import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

try:
    from alibabacloud_credentials.client import Client as CredentialClient
    from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
    from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_tea_util import models as util_models
except ImportError:
    CredentialClient = None
    dysmsapi_20170525_models = None
    Dysmsapi20170525Client = None
    open_api_models = None
    util_models = None

from app.core.config import settings

request_logger = logging.getLogger("app.request")


@dataclass
class _SmsBizCodeRecord:
    code: str
    expires_at: float


class AliSms:
    """阿里云短信网关。"""

    @staticmethod
    def create_client() -> Dysmsapi20170525Client:
        """创建阿里云短信客户端。

        :return: 阿里云短信客户端
        """
        if not all([CredentialClient, Dysmsapi20170525Client, open_api_models, util_models]):
            raise RuntimeError("阿里云短信SDK未安装")
        credential = CredentialClient()
        config = open_api_models.Config(
            access_key_id=settings.ALI_SMS_ACC_KEY,
            access_key_secret=settings.ALI_SMS_ACC_SECRET,
            credential=credential,
        )
        config.endpoint = settings.ALI_SMS_ENDPOINT
        return Dysmsapi20170525Client(config)

    @staticmethod
    async def send_async(phone: str, template_code: str, template_params: dict) -> bool:
        """发送短信验证码。

        :param phone: 手机号
        :param template_code: 模板编码
        :param template_params: 模板参数
        :return: 是否发送成功
        """
        client = AliSms.create_client()
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=settings.ALI_SMS_SIGN,
            template_code=template_code,
            template_param=json.dumps(template_params, ensure_ascii=False),
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await client.send_sms_with_options_async(send_sms_request, runtime)
            request_logger.info(f"下发短信完成: {json.dumps(resp, default=str)}")
            return True
        except Exception as error:
            request_logger.error(f"下发短信失败：{getattr(error, 'message', str(error))}")
            return False


class SmsService:
    """短信验证码服务（按手机号+业务类型限流）。"""

    def __init__(self):
        self._lock: Optional[asyncio.Lock] = None
        self._cooldown_deadline: Dict[str, float] = {}
        self._biz_codes: Dict[str, _SmsBizCodeRecord] = {}

    async def _guard_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @staticmethod
    def _biz_key(phone: str, biz_type: str) -> str:
        return f"{phone}:{biz_type}"

    @staticmethod
    def _now() -> float:
        return time.monotonic()

    def _cleanup(self, now: float) -> None:
        expired_cooldowns = [key for key, deadline in self._cooldown_deadline.items() if deadline <= now]
        for key in expired_cooldowns:
            self._cooldown_deadline.pop(key, None)

        expired_codes = [key for key, record in self._biz_codes.items() if record.expires_at <= now]
        for key in expired_codes:
            self._biz_codes.pop(key, None)

    async def send_code(self, phone: str, biz_type: str) -> Tuple[bool, int, str]:
        """发送业务验证码。

        :param phone: 手机号
        :param biz_type: 业务类型
        :return: (是否成功, 冷却秒数, 提示文案)
        """
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            key = self._biz_key(phone, biz_type)
            deadline = self._cooldown_deadline.get(key)
            if deadline and deadline > now:
                remain = max(int(deadline - now), 1)
                return False, remain, f"发送过于频繁，请{remain}秒后重试"

            code = settings.SMS_MOCK_CODE if settings.SMS_CODE_MOCK_ENABLED else f"{random.randint(100000, 999999)}"
            if settings.SMS_CODE_MOCK_ENABLED:
                sms_ok = True
            else:
                sms_ok = await AliSms.send_async(
                    phone=phone,
                    template_code=settings.ALI_SMS_VC_TEMPLATE_CODE,
                    template_params={"code": code},
                )
            if not sms_ok:
                return False, 0, "短信发送失败，请稍后重试"

            self._biz_codes[key] = _SmsBizCodeRecord(code=code, expires_at=now + settings.SMS_CODE_EXPIRE_SECONDS)
            self._cooldown_deadline[key] = now + settings.SMS_PHONE_COOLDOWN_SECONDS
            return True, settings.SMS_PHONE_COOLDOWN_SECONDS, "验证码发送成功"

    async def verify_code(self, phone: str, biz_type: str, code: str) -> bool:
        """校验业务验证码。

        :param phone: 手机号
        :param biz_type: 业务类型
        :param code: 验证码
        :return: 是否校验成功
        """
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            key = self._biz_key(phone, biz_type)
            record = self._biz_codes.get(key)
            if record is None or record.expires_at <= now:
                self._biz_codes.pop(key, None)
                return False
            if record.code != code:
                return False
            self._biz_codes.pop(key, None)
            return True


sms_service = SmsService()
