import contextlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models  # noqa: F401
from app.api.router import router
from app.core.config import settings
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
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        access_log=False,
        log_config=build_uvicorn_log_config(),
        log_level=settings.LOG_LEVEL.lower(),
    )
