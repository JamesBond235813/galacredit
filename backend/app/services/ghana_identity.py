"""Ghana Card identity provider abstraction."""

import asyncio
from typing import Any, Dict, Optional

from app.core.config import settings


class GhanaIdentityError(Exception):
    """Ghana Card identity provider error."""


class GhanaCardIdentityProvider:
    """Provide Ghana Card OCR and face comparison seams for local and production modes."""

    async def ocr(self, front_bytes: bytes, back_bytes: Optional[bytes] = None) -> Dict[str, str]:
        """识别 Ghana Card 信息。

        :param front_bytes: Ghana Card 正面图片字节
        :param back_bytes: Ghana Card 背面图片字节，可选
        :return: 包含姓名、卡号、地址和有效期的识别结果
        """
        if not front_bytes:
            raise GhanaIdentityError("Please upload the front of your Ghana Card.")
        if settings.GHANA_IDENTITY_ENABLED:
            raise GhanaIdentityError(
                "Ghana Card identity provider is reserved but not configured yet."
            )
        if settings.GHANA_IDENTITY_MOCK_ENABLED:
            await asyncio.sleep(0.05)
            return self._build_mock_ocr_result()
        raise GhanaIdentityError("Ghana Card identity verification is not enabled.")

    async def face_compare(
        self,
        name: str,
        ghana_card_number: str,
        face_image_bytes: bytes,
    ) -> Dict[str, Any]:
        """比对人脸与 Ghana Card 身份信息。

        :param name: Ghana Card 识别出的姓名
        :param ghana_card_number: Ghana Card 个人编号
        :param face_image_bytes: 人脸图片字节
        :return: 包含通过状态和分值的比对结果
        """
        if not face_image_bytes:
            raise GhanaIdentityError("Please upload a face photo.")
        if not name or not ghana_card_number:
            raise GhanaIdentityError("Ghana Card identity details are incomplete.")
        if settings.GHANA_IDENTITY_ENABLED:
            raise GhanaIdentityError(
                "Ghana Card face comparison provider is reserved but not configured yet."
            )
        if settings.GHANA_IDENTITY_MOCK_ENABLED:
            await asyncio.sleep(0.05)
            return {"passed": True, "score": 0.99, "threshold": settings.GHANA_IDENTITY_FACE_CONFIDENCE_THRESHOLD}
        raise GhanaIdentityError("Ghana Card face comparison is not enabled.")

    @staticmethod
    def _build_mock_ocr_result() -> Dict[str, str]:
        """生成开发环境使用的 Ghana Card 语义模拟结果。

        :return: Ghana Card 模拟识别结果
        """
        return {
            "name": "Ama Mensah",
            "id_card_num": "GHA-000000000-0",
            "id_address": "Accra, Ghana",
            "id_expiry": "2025.01.01-2035.01.01",
        }


ghana_card_identity_provider = GhanaCardIdentityProvider()
