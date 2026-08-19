import contextlib
import os
import sys

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401
from app.api.req_util import resolve_client_ip
from app.api.router import router
from app.core.access_audit import AccessAuditMiddleware
from app.core.database import run_async_database_bootstrap
from app.core.config import ACTIVE_PROFILE, resolve_profile, settings
from app.core.logging_config import build_uvicorn_log_config, configure_logging
from app.core.request_logging import RequestResponseLoggingMiddleware
from app.core.exceptions import BizException, biz_exception_handler, legacy_http_exception_handler
from app.services.scheduler import start_scheduler
from app.services.upload_storage import UPLOAD_ROOT


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    await run_async_database_bootstrap()
    start_scheduler()
    yield

configure_logging()
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=None,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan
)
app.add_exception_handler(BizException, biz_exception_handler)
app.add_exception_handler(HTTPException, legacy_http_exception_handler)

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestResponseLoggingMiddleware)
app.add_middleware(AccessAuditMiddleware)

app.include_router(router, prefix=settings.API_V1_STR)
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_ROOT)), name="uploads")


@app.get("/")
async def root(request: Request):
    """返回服务存活信息，并附带客户端IP。

    :param request: FastAPI 请求对象
    :return: 根路径响应字符串
    """
    # 统一复用请求IP解析工具，根接口无IP时按需求返回 *。
    client_ip = resolve_client_ip(request, default_ip="*")
    return f"hello world xhb. [{ACTIVE_PROFILE or 'default'}][{client_ip}]"


if __name__ == "__main__":
    import uvicorn
    runtime_profile = resolve_profile(sys.argv, dict(os.environ))
    if runtime_profile:
        os.environ["APP_PROFILE"] = runtime_profile

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.APP_PORT,
        reload=False,
        access_log=False,
        log_config=build_uvicorn_log_config(),
        log_level=settings.LOG_LEVEL.lower(),
    )
