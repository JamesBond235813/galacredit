import asyncio
import random
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple


@dataclass                                                                        
class _SmsCodeRecord:
    code: str
    expires_at: float


@dataclass
class _IpTokenBucket:
    tokens: float
    last_refill_at: float
    last_seen_at: float


class SmsAuthManager:
    """短信验证码下发与校验内存管理器。"""

    def __init__(
        self,
        phone_cooldown_seconds: int,
        ip_rate_limit_per_minute: int,
        code_expire_seconds: int,
        mock_enabled: bool,
        mock_code: str,
        now_provider: Optional[Callable[[], float]] = None,
    ):
        self.phone_cooldown_seconds = max(int(phone_cooldown_seconds), 1)
        self.ip_rate_limit_per_minute = max(int(ip_rate_limit_per_minute), 1)
        self.code_expire_seconds = max(int(code_expire_seconds), 1)
        self.mock_enabled = bool(mock_enabled)
        self.mock_code = mock_code
        self._now_provider = now_provider or time.monotonic
        self._lock = asyncio.Lock()
        self._phone_cooldown_deadline: Dict[str, float] = {}
        self._phone_codes: Dict[str, _SmsCodeRecord] = {}
        self._ip_buckets: Dict[str, _IpTokenBucket] = {}

    def _now(self) -> float:
        return float(self._now_provider())

    def _cleanup(self, now: float) -> None:
        """清理过期状态，避免内存随着请求增长而泄漏。"""
        expired_phones = [phone for phone, deadline in self._phone_cooldown_deadline.items() if deadline <= now]
        for phone in expired_phones:
            self._phone_cooldown_deadline.pop(phone, None)

        expired_codes = [phone for phone, record in self._phone_codes.items() if record.expires_at <= now]
        for phone in expired_codes:
            self._phone_codes.pop(phone, None)

        expire_ip_after = max(self.phone_cooldown_seconds * 2, 120)
        expired_ips = [ip for ip, bucket in self._ip_buckets.items() if now - bucket.last_seen_at >= expire_ip_after]
        for ip in expired_ips:
            self._ip_buckets.pop(ip, None)

    def _consume_ip_token(self, ip: str, now: float) -> bool:
        capacity = float(self.ip_rate_limit_per_minute)
        refill_rate_per_second = capacity / 60.0
        bucket = self._ip_buckets.get(ip)
        if bucket is None:
            bucket = _IpTokenBucket(tokens=capacity, last_refill_at=now, last_seen_at=now)
            self._ip_buckets[ip] = bucket

        elapsed = max(0.0, now - bucket.last_refill_at)
        if elapsed > 0:
            bucket.tokens = min(capacity, bucket.tokens + elapsed * refill_rate_per_second)
            bucket.last_refill_at = now
        bucket.last_seen_at = now

        if bucket.tokens >= 1.0:
            bucket.tokens -= 1.0
            return True
        return False

    async def issue_code(self, phone: str, ip: str) -> Tuple[bool, int]:
        """申请发送短信验证码。

        :param phone: 手机号
        :param ip: 请求方IP
        :return: (是否成功, 冷却剩余秒数)
        """
        async with self._lock:
            now = self._now()
            self._cleanup(now)

            cooldown_deadline = self._phone_cooldown_deadline.get(phone)
            if cooldown_deadline and cooldown_deadline > now:
                remain = int(cooldown_deadline - now)
                return False, max(remain, 1)

            if not self._consume_ip_token(ip, now):
                return False, self.phone_cooldown_seconds

            # 统一在此刷新验证码，确保验证码生命周期与发送动作强绑定。
            code = self.mock_code if self.mock_enabled else f"{random.randint(100000, 999999)}"
            self._phone_codes[phone] = _SmsCodeRecord(code=code, expires_at=now + self.code_expire_seconds)
            self._phone_cooldown_deadline[phone] = now + self.phone_cooldown_seconds
            return True, self.phone_cooldown_seconds

    async def verify_code(self, phone: str, code: str) -> bool:
        """校验短信验证码。

        :param phone: 手机号
        :param code: 用户输入验证码
        :return: 是否校验成功
        """
        async with self._lock:
            now = self._now()
            self._cleanup(now)
            record = self._phone_codes.get(phone)
            if record is None:
                return False
            if record.expires_at <= now:
                self._phone_codes.pop(phone, None)
                return False
            if record.code != code:
                return False
            self._phone_codes.pop(phone, None)
            return True

    async def debug_state_size(self) -> Tuple[int, int, int]:
        """返回当前内存状态规模，仅用于单元测试。"""
        async with self._lock:
            now = self._now()
            self._cleanup(now)
            return len(self._phone_cooldown_deadline), len(self._phone_codes), len(self._ip_buckets)
