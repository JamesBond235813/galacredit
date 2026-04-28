import json
import logging
from datetime import datetime
from logging.config import dictConfig
from pathlib import Path
from time import gmtime
from zoneinfo import ZoneInfo

from app.core.config import settings
from app.core.trace import get_trace_id


class TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.tid = get_trace_id()
        return True


class TZFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        tz_name = settings.LOG_TZ or "Asia/Shanghai"
        dt = datetime.fromtimestamp(record.created, tz=ZoneInfo(tz_name))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


class JsonFormatter(logging.Formatter):
    converter = gmtime

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "service": settings.PROJECT_NAME,
            "env": "default",
            "tid": getattr(record, "tid", "-"),
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name,
        }
        if hasattr(record, "method"):
            payload["method"] = getattr(record, "method")
        if hasattr(record, "url"):
            payload["url"] = getattr(record, "url")
        if hasattr(record, "status_code"):
            payload["status_code"] = getattr(record, "status_code")
        if hasattr(record, "duration_ms"):
            payload["duration_ms"] = getattr(record, "duration_ms")
        if record.exc_info:
            payload["exception_type"] = record.exc_info[0].__name__ if record.exc_info[0] else "Exception"
        return json.dumps(payload, ensure_ascii=False)


_CONFIGURED = False


def _formatter_name() -> str:
    return "json" if (settings.LOG_OUTPUT or "txt").lower() == "json" else "txt"


def _formatter_config() -> dict:
    return {
        "txt": {
            "()": "app.core.logging_config.TZFormatter",
            "format": settings.LOG_FORMATTER,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {"()": "app.core.logging_config.JsonFormatter"},
    }


def _build_timed_file_handler(filename: str, formatter: str, level: str) -> dict:
    return {
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": filename,
        "when": "midnight",
        "interval": 1,
        "backupCount": max(int(settings.LOG_RETENTION_DAYS or 90), 1),
        "encoding": "utf-8",
        "formatter": formatter,
        "filters": ["tid_filter"],
        "level": level,
    }


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    level = (settings.LOG_LEVEL or "INFO").upper()
    formatter_name = _formatter_name()

    app_file = str(log_dir / (settings.LOG_APP_FILE or settings.LOG_FILE_NAME or "app.log"))
    request_file = str(log_dir / (settings.LOG_REQUEST_FILE or "request.log"))
    response_file = str(log_dir / (settings.LOG_RESPONSE_FILE or "response.log"))
    error_file = str(log_dir / (settings.LOG_ERROR_FILE or "error.log"))

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"tid_filter": {"()": "app.core.logging_config.TraceIdFilter"}},
            "formatters": _formatter_config(),
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter_name,
                    "filters": ["tid_filter"],
                    "level": level,
                },
                "app_file": _build_timed_file_handler(app_file, formatter_name, level),
                "request_file": _build_timed_file_handler(request_file, formatter_name, level),
                "response_file": _build_timed_file_handler(response_file, formatter_name, level),
                "error_file": _build_timed_file_handler(error_file, formatter_name, level),
            },
            "loggers": {
                "": {"handlers": ["console", "app_file"], "level": level},
                "uvicorn": {"handlers": ["console", "app_file"], "level": level, "propagate": False},
                "uvicorn.error": {"handlers": ["console", "app_file", "error_file"], "level": level, "propagate": False},
                "uvicorn.access": {"handlers": [], "level": level, "propagate": False},
                "app.request": {"handlers": ["console", "request_file"], "level": level, "propagate": False},
                "app.response": {"handlers": ["console", "response_file"], "level": level, "propagate": False},
                "app.error": {"handlers": ["console", "error_file"], "level": level, "propagate": False},
            },
        }
    )
    _CONFIGURED = True


def build_uvicorn_log_config() -> dict:
    return {"version": 1, "disable_existing_loggers": False}
