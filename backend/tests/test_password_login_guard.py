import pytest

from app.services.password_login_guard import PasswordLoginGuard


class _Clock:
    def __init__(self):
        self.value = 0.0

    def now(self):
        return self.value

    def step(self, seconds: float):
        self.value += seconds


@pytest.mark.asyncio
async def test_password_login_guard_should_freeze_phone_after_five_failures():
    clock = _Clock()
    guard = PasswordLoginGuard(
        max_attempts=5,
        window_seconds=300,
        freeze_seconds=1800,
        now_provider=clock.now,
    )

    for _ in range(4):
        frozen_minutes = await guard.before_verify("13800000000")
        assert frozen_minutes == 0
        await guard.on_failure("13800000000")

    assert await guard.before_verify("13800000000") == 0
    await guard.on_failure("13800000000")
    assert await guard.before_verify("13800000000") == 30

    clock.step(60)
    assert await guard.before_verify("13800000000") == 29

    clock.step(1800)
    assert await guard.before_verify("13800000000") == 0


@pytest.mark.asyncio
async def test_password_login_guard_should_cleanup_expired_state():
    clock = _Clock()
    guard = PasswordLoginGuard(
        max_attempts=5,
        window_seconds=300,
        freeze_seconds=1800,
        now_provider=clock.now,
    )

    await guard.on_failure("13800000001")
    await guard.on_failure("13800000002")
    assert await guard.debug_state_size() == 2

    clock.step(2200)
    assert await guard.before_verify("13800000003") == 0
    assert await guard.debug_state_size() == 0
