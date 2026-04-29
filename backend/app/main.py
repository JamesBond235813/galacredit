import contextlib
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.router import router
from app.core.config import ACTIVE_PROFILE, resolve_profile, settings
from app.core.logging_config import build_uvicorn_log_config, configure_logging
from app.core.request_logging import RequestResponseLoggingMiddleware
from app.services.scheduler import start_scheduler


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
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

# 跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestResponseLoggingMiddleware)

app.include_router(router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return f"hello world xhb. [{ACTIVE_PROFILE or 'default'}]"


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
