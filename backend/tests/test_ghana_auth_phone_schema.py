import pytest
from pydantic import ValidationError

from app.schemas.user import SendCodeRequest, SliderCaptchaCreateRequest, SmsLoginRequest


@pytest.mark.parametrize(
    "schema,payload",
    [
        (SendCodeRequest, {"phone": "233240000001", "captcha_ticket": "captcha-ticket-01"}),
        (SliderCaptchaCreateRequest, {"phone": "233240000001", "width": 360}),
        (SmsLoginRequest, {"phone": "233240000001", "sms_code": "635147"}),
    ],
)
def test_auth_schemas_should_accept_ghana_international_phone(schema, payload):
    """验证认证请求接受加纳国际号码。

    :param schema: 请求模型类
    :param payload: 请求数据
    :return: None
    """
    assert schema(**payload).phone == "233240000001"


def test_auth_schema_should_keep_legacy_phone_compatibility():
    """验证认证请求继续兼容历史十一位号码。

    :return: None
    """
    request = SmsLoginRequest(phone="13800000000", sms_code="635147")
    assert request.phone == "13800000000"


@pytest.mark.parametrize("phone", ["240000001", "0233240000001", "2332400000019"])
def test_auth_schema_should_reject_invalid_phone(phone):
    """验证认证请求拒绝长度或前缀错误的号码。

    :param phone: 待验证手机号
    :return: None
    """
    with pytest.raises(ValidationError):
        SmsLoginRequest(phone=phone, sms_code="635147")
