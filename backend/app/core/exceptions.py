from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class BizException(HTTPException):
    """业务异常，业务失败使用统一 code/msg 返回。"""

    def __init__(self, message: str, code: int = 400, *, http_status: Optional[int] = None, headers: Optional[dict] = None):
        self.message = message
        self.code = code
        self.http_status = http_status if http_status is not None else (401 if code == 401 else 200)
        self.headers = headers or {}
        super().__init__(status_code=self.http_status, detail=message, headers=self.headers)


async def biz_exception_handler(request: Request, exc: BizException) -> JSONResponse:
    """将业务异常转换为统一响应。

    :param request: FastAPI 请求
    :param exc: 业务异常
    :return: 统一 JSON 响应
    """
    return JSONResponse(status_code=exc.http_status, content={"code": exc.code, "msg": exc.message}, headers=exc.headers)


async def legacy_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """兼容旧路由异常，避免再返回 FastAPI detail 结构。

    :param request: FastAPI 请求
    :param exc: 历史 HTTP 异常
    :return: 统一 JSON 响应
    """
    code = int(exc.status_code or 400)
    http_status = code if code == 401 else 200
    return JSONResponse(status_code=http_status, content={"code": code, "msg": str(exc.detail)}, headers=exc.headers or {})
