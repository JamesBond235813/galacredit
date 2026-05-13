import json
import logging
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from app.core.config import settings
from app.core.trace import new_trace_id, reset_trace_id, set_trace_id

request_logger = logging.getLogger("app.request")
response_logger = logging.getLogger("app.response")
error_logger = logging.getLogger("app.error")

_SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "token",
    "password",
    "code",
    "sms_code",
    "captcha_ticket",
    "id_card_num",
    "idcard",
    "id_card",
    "card_no",
    "card_secret",
    "secret",
    "app_secret",
    "face_image",
    "front_image",
    "back_image",
}
_HEADER_ALLOWLIST = {
    "host",
    "user-agent",
    "content-type",
    "content-length",
    "x-forwarded-for",
    "x-real-ip",
    "x-trace-id",
    "client-id",
}


def _mask_value(value: Any) -> str:
    text = "" if value is None else str(value)
    if len(text) <= 4:
        return "***"
    return f"{text[:2]}***{text[-2:]}"


def _redact_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        redacted = {}
        for key, value in payload.items():
            lower_key = str(key).lower()
            if any(sensitive in lower_key for sensitive in _SENSITIVE_KEYS):
                redacted[key] = _mask_value(value)
            else:
                redacted[key] = _redact_payload(value)
        return redacted
    if isinstance(payload, list):
        return [_redact_payload(item) for item in payload]
    return payload


def _safe_headers(headers: dict) -> dict:
    safe = {}
    for key, value in headers.items():
        lower_key = key.lower()
        if lower_key in _HEADER_ALLOWLIST:
            safe[key] = value
        elif any(sensitive in lower_key for sensitive in _SENSITIVE_KEYS):
            safe[key] = "***"
    return safe


def _safe_json_text(data: bytes) -> str:
    if not data:
        return ""
    try:
        parsed: Any = json.loads(data.decode("utf-8"))
        parsed = _redact_payload(parsed)
        return json.dumps(parsed, ensure_ascii=False)
    except Exception:
        return "[NON_JSON_BODY]"


def _is_upload_request(content_type: str) -> bool:
    lower_type = (content_type or "").lower()
    return "multipart/form-data" in lower_type


def _is_download_response(content_type: str, content_disposition: str) -> bool:
    lower_type = (content_type or "").lower()
    lower_disposition = (content_disposition or "").lower()
    return (
        "attachment" in lower_disposition
        or "application/octet-stream" in lower_type
        or "application/vnd.ms-excel" in lower_type
        or "application/vnd.openxmlformats-officedocument" in lower_type
    )

def _should_skip_response_body_log(path: str) -> bool:
    normalized = (path or "").strip()
    return normalized.startswith("/api/auth/slider-captcha/")


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_header = settings.TID_HEADER_NAME or "X-Trace-Id"
        trace_id = request.headers.get(trace_header) or new_trace_id()
        token = set_trace_id(trace_id)
        request.state.trace_id = trace_id
        started = time.perf_counter()

        body = await request.body()
        headers = _safe_headers(dict(request.headers))
        content_type = headers.get("content-type", "")
        if not settings.LOG_REQUEST_BODY_ENABLED:
            request_body = "[DISABLED]"
        elif _is_upload_request(content_type):
            request_body = "[UPLOAD FILE CONTENT]"
        else:
            request_body = _safe_json_text(body)

        async def receive():
            return {"type": "http.request", "body": body, "more_body": False}

        request = Request(request.scope, receive)
        url_with_query = str(request.url)
        should_log = request.method.upper() != "OPTIONS"
        if should_log:
            request_logger.info(
                "request_data method=%s url=%s headers=%s body=%s",
                request.method,
                url_with_query,
                json.dumps(headers, ensure_ascii=False),
                request_body,
                extra={"method": request.method, "url": url_with_query},
            )

        try:
            response = await call_next(request)
            response.headers[trace_header] = trace_id

            raw_response_headers = dict(response.headers)
            response_headers = _safe_headers(raw_response_headers)
            response_content_type = response_headers.get("content-type", "")
            content_disposition = response_headers.get("content-disposition", "")
            skip_response_log = _should_skip_response_body_log(request.url.path)

            if not settings.LOG_RESPONSE_BODY_ENABLED:
                response_body = "[DISABLED]"
            elif skip_response_log:
                response_body = "[SKIPPED]"
            elif _is_download_response(response_content_type, content_disposition):
                response_body = "[DOWNLOAD FILE CONTENT]"
            else:
                response_chunks = [chunk async for chunk in response.body_iterator]
                response_raw = b"".join(response_chunks)
                response_body = _safe_json_text(response_raw)
                response = StarletteResponse(
                    content=response_raw,
                    status_code=response.status_code,
                    headers=raw_response_headers,
                    media_type=response.media_type,
                    background=response.background,
                )

            if should_log and not skip_response_log:
                response_logger.info(
                    "response_data method=%s url=%s status=%s headers=%s body=%s",
                    request.method,
                    url_with_query,
                    response.status_code,
                    json.dumps(response_headers, ensure_ascii=False),
                    response_body,
                    extra={
                        "method": request.method,
                        "url": url_with_query,
                        "status_code": response.status_code,
                        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    },
                )
            return response
        except Exception:
            error_logger.exception(
                "request_exception method=%s url=%s",
                request.method,
                url_with_query,
                extra={"method": request.method, "url": url_with_query},
            )
            raise
        finally:
            reset_trace_id(token)
