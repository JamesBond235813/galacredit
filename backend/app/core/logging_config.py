import logging
from logging.config import dictConfig
from pathlib import Path

from app.core.config import settings
from app.core.trace import get_trace_id


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = get_trace_id()
        return True


def configure_logging() -> None:
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / settings.LOG_FILE_NAME
    level = (settings.LOG_LEVEL or "INFO").upper()

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"trace_id_filter": {"()": "app.core.logging_config.TraceIdFilter"}},
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | trace_id=%(trace_id)s | %(message)s"
                }
            },
            "handlers": {
                "default_file": {
                    "class": "logging.FileHandler",
                    "filename": str(log_path),
                    "encoding": "utf-8",
                    "formatter": "default",
                    "filters": ["trace_id_filter"],
                },
                "default_console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["trace_id_filter"],
                },
            },
            "loggers": {
                "": {"handlers": ["default_console", "default_file"], "level": level},
                "uvicorn": {"handlers": ["default_console", "default_file"], "level": level, "propagate": False},
                "uvicorn.error": {"handlers": ["default_console", "default_file"], "level": level, "propagate": False},
                "uvicorn.access": {"handlers": [], "level": level, "propagate": False},
                "app.request": {"handlers": ["default_console", "default_file"], "level": level, "propagate": False},
            },
        }
    )


def build_uvicorn_log_config() -> dict:
    # 交给应用级 dictConfig 统一托管，uvicorn 启动时直接复用。
    return {"version": 1, "disable_existing_loggers": False}
