# -*- coding: utf-8 -*-
# created by liwei
# created at 2026/4/29 11:42
# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import json
import logging

import pytest
from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
from alibabacloud_dysmsapi20170525.client import Client as Dysmsapi20170525Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from app.core.config import settings

request_logger = logging.getLogger("app.request")


class AliSms:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Dysmsapi20170525Client:
        """
        使用凭据初始化账号Client
        @return: Client
        @throws Exception
        """
        # 工程代码建议使用更安全的无AK方式，凭据配置方式请参见：https://help.aliyun.com/document_detail/378659.html。
        credential = CredentialClient()
        config = open_api_models.Config(
            access_key_id=settings.ALI_SMS_ACC_KEY,
            access_key_secret=settings.ALI_SMS_ACC_SECRET,
            credential=credential
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Dysmsapi
        config.endpoint = settings.ALI_SMS_ENDPOINT
        return Dysmsapi20170525Client(config)

    @staticmethod
    async def send_async(phone: str, template_code: str, template_params: dict = {}) -> bool:
        client = AliSms.create_client()
        send_sms_request = dysmsapi_20170525_models.SendSmsRequest(
            phone_numbers=phone,
            sign_name=settings.ALI_SMS_SIGN,
            template_code=template_code,
            template_param=json.dumps(template_params, ensure_ascii=False)
        )
        runtime = util_models.RuntimeOptions()
        try:
            resp = await client.send_sms_with_options_async(send_sms_request, runtime)
            request_logger.info(f'下发短信完成: {json.dumps(resp, default=str)}')
            return True
        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            request_logger.error(f'下发短信失败： {error.message} - {error.data and error.data.get("Recommend")}')
        return False


@pytest.mark.asyncio
async def test_sms_send():
    phone: str = '18668105693'
    template_code = settings.ALI_SMS_VC_TEMPLATE_CODE
    template_params = {"code": "1234"}
    await AliSms.send_async(phone=phone, template_code=template_code, template_params=template_params)
