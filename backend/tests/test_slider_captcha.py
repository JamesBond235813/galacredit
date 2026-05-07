import pytest

from app.services.slider_captcha import SliderCaptchaManager


@pytest.mark.asyncio
async def test_slider_captcha_should_expire_after_max_failures():
    manager = SliderCaptchaManager(
        tolerance_px=5,
        min_elapsed_ms=100,
        challenge_expire_seconds=180,
        challenge_max_fails=3,
        ticket_expire_seconds=180,
        min_width=280,
        max_width=420,
        height=160,
        block_size=44,
    )

    payload = await manager.create_challenge(320)
    captcha_id = payload["captcha_id"]

    with pytest.raises(ValueError) as e1:
        await manager.verify_challenge("13800000000", captcha_id, offset_x=0, elapsed_ms=350)
    assert "滑块位置不正确" in str(e1.value)

    with pytest.raises(ValueError) as e2:
        await manager.verify_challenge("13800000000", captcha_id, offset_x=0, elapsed_ms=350)
    assert "滑块位置不正确" in str(e2.value)

    with pytest.raises(ValueError) as e3:
        await manager.verify_challenge("13800000000", captcha_id, offset_x=0, elapsed_ms=350)
    assert "已失效" in str(e3.value)
