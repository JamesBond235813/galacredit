import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class _ChallengeRecord:
    expected_x: int
    created_at: float
    fail_count: int


@dataclass
class _TicketRecord:
    phone: str
    expires_at: float


class SliderCaptchaManager:
    """滑块验证码内存管理器。"""

    def __init__(
        self,
        *,
        tolerance_px: int,
        min_elapsed_ms: int,
        challenge_expire_seconds: int,
        challenge_max_fails: int,
        ticket_expire_seconds: int,
        min_width: int,
        max_width: int,
        height: int,
        block_size: int,
        max_cache_size: int = 5000,
    ):
        self.tolerance_px = max(int(tolerance_px), 1)
        self.min_elapsed_ms = max(int(min_elapsed_ms), 300)
        self.challenge_expire_seconds = max(int(challenge_expire_seconds), 30)
        self.challenge_max_fails = max(int(challenge_max_fails), 1)
        self.ticket_expire_seconds = max(int(ticket_expire_seconds), 30)
        self.min_width = max(int(min_width), 200)
        self.max_width = max(int(max_width), self.min_width)
        self.height = max(int(height), 100)
        self.block_size = max(int(block_size), 24)
        self.max_cache_size = max(int(max_cache_size), 100)
        self._lock: Optional[asyncio.Lock] = None
        self._challenges: Dict[str, _ChallengeRecord] = {}
        self._tickets: Dict[str, _TicketRecord] = {}

    async def _guard_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    @staticmethod
    def _now() -> float:
        return time.monotonic()

    def _cleanup(self, now: float) -> None:
        expired_challenges = [
            captcha_id
            for captcha_id, record in self._challenges.items()
            if now - record.created_at >= self.challenge_expire_seconds
        ]
        for captcha_id in expired_challenges:
            self._challenges.pop(captcha_id, None)

        expired_tickets = [ticket for ticket, record in self._tickets.items() if record.expires_at <= now]
        for ticket in expired_tickets:
            self._tickets.pop(ticket, None)

        # 限制缓存上限，避免异常流量下内存持续增长
        if len(self._challenges) > self.max_cache_size:
            overflow = len(self._challenges) - self.max_cache_size
            stale_ids = sorted(self._challenges.items(), key=lambda item: item[1].created_at)[:overflow]
            for captcha_id, _ in stale_ids:
                self._challenges.pop(captcha_id, None)
        if len(self._tickets) > self.max_cache_size:
            overflow = len(self._tickets) - self.max_cache_size
            stale_tickets = sorted(self._tickets.items(), key=lambda item: item[1].expires_at)[:overflow]
            for ticket, _ in stale_tickets:
                self._tickets.pop(ticket, None)

    def _clamp_width(self, width: int) -> int:
        return min(max(int(width), self.min_width), self.max_width)

    async def create_challenge(self, width: int) -> dict:
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            effective_width = self._clamp_width(width)
            expected_x = max(effective_width - self.block_size, 0)
            expected_y = (self.height - self.block_size) // 2
            captcha_id = uuid.uuid4().hex
            self._challenges[captcha_id] = _ChallengeRecord(expected_x=expected_x, created_at=now, fail_count=0)
            return {
                "captcha_id": captcha_id,
                "width": effective_width,
                "height": self.block_size,
                "block_size": self.block_size,
                "block_y": expected_y,
                "background_image": "",
                "slider_image": "",
                "min_elapsed_ms": self.min_elapsed_ms,
            }

    async def verify_challenge(self, phone: str, captcha_id: str, offset_x: float, elapsed_ms: int) -> str:
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            record = self._challenges.get(captcha_id)
            if record is None:
                raise ValueError("图形验证码已过期，请刷新重试")
            if int(elapsed_ms) < self.min_elapsed_ms:
                record.fail_count += 1
                if record.fail_count >= self.challenge_max_fails:
                    self._challenges.pop(captcha_id, None)
                    raise ValueError("图形验证码已失效，请刷新重试")
                raise ValueError("滑动过快，请重新验证")
            if abs(float(offset_x) - float(record.expected_x)) > float(self.tolerance_px):
                record.fail_count += 1
                if record.fail_count >= self.challenge_max_fails:
                    self._challenges.pop(captcha_id, None)
                    raise ValueError("图形验证码已失效，请刷新重试")
                raise ValueError("滑块位置不正确，请重试")

            ticket = uuid.uuid4().hex
            self._tickets[ticket] = _TicketRecord(phone=phone, expires_at=now + self.ticket_expire_seconds)
            self._challenges.pop(captcha_id, None)
            return ticket

    async def consume_ticket(self, phone: str, ticket: str) -> bool:
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            record = self._tickets.pop(ticket, None)
            if record is None:
                return False
            return record.phone == phone and record.expires_at > now
