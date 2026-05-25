import asyncio
from cachetools import TTLCache

_LOAN_SNAPSHOT_VERSION_BY_USER = TTLCache(maxsize=200000, ttl=60 * 60 * 6)


def _get_loan_snapshot_version(user_id: int) -> int:
    _LOAN_SNAPSHOT_VERSION_BY_USER.expire()
    return int(_LOAN_SNAPSHOT_VERSION_BY_USER.get(int(user_id), 0))


async def notify_loan_snapshot_changed(user_id: int):
    """标记指定用户的订单快照已变化。"""
    key = int(user_id)
    _LOAN_SNAPSHOT_VERSION_BY_USER.expire()
    _LOAN_SNAPSHOT_VERSION_BY_USER[key] = _get_loan_snapshot_version(key) + 1


async def wait_loan_snapshot_changed(user_id: int, last_version: int, timeout_seconds: float):
    """等待用户订单快照版本变化；超时则返回当前版本。"""
    key = int(user_id)
    current_version = _get_loan_snapshot_version(key)
    if current_version != int(last_version):
        return current_version

    deadline = asyncio.get_running_loop().time() + max(float(timeout_seconds or 0), 0)
    while asyncio.get_running_loop().time() < deadline:
        await asyncio.sleep(0.5)
        current_version = _get_loan_snapshot_version(key)
        if current_version != int(last_version):
            return current_version
    return current_version
