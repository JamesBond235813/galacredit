import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from math import ceil
from typing import Callable, Deque, Dict, Optional


@dataclass
class _PhoneLoginState:
    failures: Deque[float] = field(default_factory=deque)
    freeze_until: float = 0.0
    last_seen_at: float = 0.0


class PasswordLoginGuard:
    """手机号密码登录失败风控管理器。"""

    def __init__(
        self,
        max_attempts: int,
        window_seconds: int,
        freeze_seconds: int,
        now_provider: Optional[Callable[[], float]] = None,
    ):
        self.max_attempts = max(int(max_attempts), 1)
        self.window_seconds = max(int(window_seconds), 1)
        self.freeze_seconds = max(int(freeze_seconds), 1)
        self._now_provider = now_provider or time.monotonic
        self._lock: Optional[asyncio.Lock] = None
        self._phone_states: Dict[str, _PhoneLoginState] = {}

    def _now(self) -> float:
        return float(self._now_provider())

    def _cleanup(self, now: float) -> None:
        """清理过期手机号状态，避免内存泄漏。"""
        max_keep_seconds = self.freeze_seconds + self.window_seconds + 60
        expired_phones = []
        for phone, state in self._phone_states.items():
            while state.failures and state.failures[0] <= now - self.window_seconds:
                state.failures.popleft()
            if state.freeze_until <= now and not state.failures and now - state.last_seen_at >= max_keep_seconds:
                expired_phones.append(phone)
        for phone in expired_phones:
            self._phone_states.pop(phone, None)

    async def _guard_lock(self) -> asyncio.Lock:
        """获取异步锁，延迟初始化以兼容同步测试场景。"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def before_verify(self, phone: str) -> int:
        """登录校验前判断手机号是否已冻结。

        :param phone: 手机号
        :return: 冻结剩余分钟；0 表示未冻结
        """
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            state = self._phone_states.get(phone)
            if state is None:
                return 0
            state.last_seen_at = now
            remain_seconds = state.freeze_until - now
            if remain_seconds <= 0:
                return 0
            return max(1, int(ceil(remain_seconds / 60.0)))

    async def on_failure(self, phone: str) -> int:
        """记录一次密码失败并返回冻结剩余分钟。

        :param phone: 手机号
        :return: 冻结剩余分钟；0 表示未冻结
        """
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            state = self._phone_states.get(phone)
            if state is None:
                state = _PhoneLoginState(last_seen_at=now)
                self._phone_states[phone] = state
            state.last_seen_at = now

            # 已冻结期间不重复累计，避免同一冻结窗口内状态持续膨胀。
            if state.freeze_until > now:
                remain_seconds = state.freeze_until - now
                return max(1, int(ceil(remain_seconds / 60.0)))

            state.failures.append(now)
            while state.failures and state.failures[0] <= now - self.window_seconds:
                state.failures.popleft()

            if len(state.failures) >= self.max_attempts:
                state.freeze_until = now + self.freeze_seconds
                state.failures.clear()
                return max(1, int(ceil(self.freeze_seconds / 60.0)))
            return 0

    async def on_success(self, phone: str) -> None:
        """登录成功后清理该手机号风控状态。

        :param phone: 手机号
        :return: None
        """
        lock = await self._guard_lock()
        async with lock:
            self._phone_states.pop(phone, None)

    async def debug_state_size(self) -> int:
        """返回当前手机号状态数量，仅用于测试。"""
        lock = await self._guard_lock()
        async with lock:
            now = self._now()
            self._cleanup(now)
            return len(self._phone_states)
