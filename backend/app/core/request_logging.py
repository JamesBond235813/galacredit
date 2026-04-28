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


def _safe_json_text(data: bytes) -> str:
    if not data:
        return ""
    try:
        parsed: Any = json.loads(data.decode("utf-8"))
        return json.dumps(parsed, ensure_ascii=False)
    except Exception:
        return data.decode("utf-8", errors="replace")


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


class RequestResponseLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_header = settings.TID_HEADER_NAME or "X-Trace-Id"
        trace_id = request.headers.get(trace_header) or new_trace_id()
        token = set_trace_id(trace_id)
        request.state.trace_id = trace_id
        started = time.perf_counter()

        body = await request.body()
        headers = dict(request.headers)
        content_type = headers.get("content-type", "")
        request_body = "[UPLOAD FILE CONTENT]" if _is_upload_request(content_type) else _safe_json_text(body)

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

            response_headers = dict(response.headers)
            response_content_type = response_headers.get("content-type", "")
            content_disposition = response_headers.get("content-disposition", "")

            if _is_download_response(response_content_type, content_disposition):
                response_body = "[DOWNLOAD FILE CONTENT]"
            else:
                response_chunks = [chunk async for chunk in response.body_iterator]
                response_raw = b"".join(response_chunks)
                response_body = _safe_json_text(response_raw)
                response = StarletteResponse(
                    content=response_raw,
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type=response.media_type,
                    background=response.background,
                )

            if should_log:
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
