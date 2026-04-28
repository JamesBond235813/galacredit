import pytest

from app.services.sms_auth import SmsAuthManager


class _Clock:
    def __init__(self):
        self.value = 0.0

    def now(self):
        return self.value

    def step(self, seconds: float):
        self.value += seconds


@pytest.mark.asyncio
async def test_sms_auth_manager_should_enforce_phone_cooldown_and_verify_code():
    clock = _Clock()
    manager = SmsAuthManager(
        phone_cooldown_seconds=60,
        ip_rate_limit_per_minute=10,
        code_expire_seconds=300,
        mock_enabled=True,
        mock_code="635147",
        now_provider=clock.now,
    )

    success, remain = await manager.issue_code("13800000000", "127.0.0.1")
    assert success is True
    assert remain == 60

    second_success, second_remain = await manager.issue_code("13800000000", "127.0.0.1")
    assert second_success is False
    assert second_remain == 60

    assert await manager.verify_code("13800000000", "123456") is False
    assert await manager.verify_code("13800000000", "635147") is True
    assert await manager.verify_code("13800000000", "635147") is False


@pytest.mark.asyncio
async def test_sms_auth_manager_should_enforce_ip_token_bucket_and_cleanup():
    clock = _Clock()
    manager = SmsAuthManager(
        phone_cooldown_seconds=60,
        ip_rate_limit_per_minute=2,
        code_expire_seconds=5,
        mock_enabled=True,
        mock_code="635147",
        now_provider=clock.now,
    )

    assert (await manager.issue_code("13800000001", "10.0.0.1"))[0] is True
    assert (await manager.issue_code("13800000002", "10.0.0.1"))[0] is True
    assert (await manager.issue_code("13800000003", "10.0.0.1"))[0] is False

    clock.step(180)
    cooldown_size, code_size, ip_size = await manager.debug_state_size()
    assert cooldown_size == 0
    assert code_size == 0
    assert ip_size == 0
