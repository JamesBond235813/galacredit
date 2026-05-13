import io
import logging

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from app.core.request_logging import RequestResponseLoggingMiddleware


def _build_app():
    app = FastAPI()
    app.add_middleware(RequestResponseLoggingMiddleware)

    @app.post("/echo")
    async def echo(payload: dict):
        return {"received": payload}

    @app.post("/upload")
    async def upload(file: UploadFile = File(...)):
        content = await file.read()
        return {"size": len(content)}

    @app.get("/download")
    async def download():
        stream = io.BytesIO(b"fake-binary-content")
        return StreamingResponse(
            stream,
            media_type="application/octet-stream",
            headers={"Content-Disposition": "attachment; filename=test.bin"},
        )

    @app.options("/echo")
    async def echo_options():
        return {"ok": True}

    @app.post("/api/auth/slider-captcha/create")
    async def slider_create():
        return {
            "captcha_id": "abc",
            "background_image": "data:image/svg+xml;base64,xxx",
            "slider_image": "data:image/svg+xml;base64,yyy",
        }

    return app


def test_request_response_log_contains_trace_id_and_url(caplog, monkeypatch):
    monkeypatch.setattr("app.core.request_logging.settings.LOG_REQUEST_BODY_ENABLED", True)
    monkeypatch.setattr("app.core.request_logging.settings.LOG_RESPONSE_BODY_ENABLED", True)
    caplog.set_level(logging.INFO)
    client = TestClient(_build_app())

    response = client.post("/echo?from=h5", json={"hello": "world"}, headers={"x-test-header": "demo"})
    assert response.status_code == 200
    assert "x-trace-id" in response.headers

    request_logs = [r.message for r in caplog.records if "request_data" in r.message]
    response_logs = [r.message for r in caplog.records if "response_data" in r.message]
    assert request_logs
    assert response_logs
    assert "/echo?from=h5" in request_logs[-1]
    assert '"hello": "world"' in request_logs[-1]
    assert "/echo?from=h5" in response_logs[-1]
    assert '"received"' in response_logs[-1]


def test_upload_and_download_content_should_be_masked(caplog, monkeypatch):
    monkeypatch.setattr("app.core.request_logging.settings.LOG_REQUEST_BODY_ENABLED", True)
    monkeypatch.setattr("app.core.request_logging.settings.LOG_RESPONSE_BODY_ENABLED", True)
    caplog.set_level(logging.INFO)
    client = TestClient(_build_app())

    upload_response = client.post("/upload", files={"file": ("a.txt", b"abc", "text/plain")})
    assert upload_response.status_code == 200

    download_response = client.get("/download")
    assert download_response.status_code == 200

    request_logs = [r.message for r in caplog.records if "request_data" in r.message]
    response_logs = [r.message for r in caplog.records if "response_data" in r.message]
    assert any("[UPLOAD FILE CONTENT]" in m for m in request_logs)
    assert any("[DOWNLOAD FILE CONTENT]" in m for m in response_logs)


def test_options_request_should_not_print_request_or_response_log(caplog):
    caplog.set_level(logging.INFO)
    client = TestClient(_build_app())

    response = client.options("/echo")
    assert response.status_code == 200

    request_logs = [r.message for r in caplog.records if "request_data" in r.message]
    response_logs = [r.message for r in caplog.records if "response_data" in r.message]
    assert all("/echo" not in item for item in request_logs)
    assert all("/echo" not in item for item in response_logs)


def test_slider_captcha_response_should_not_print_response_log(caplog):
    caplog.set_level(logging.INFO)
    client = TestClient(_build_app())

    response = client.post("/api/auth/slider-captcha/create")
    assert response.status_code == 200

    request_logs = [r.message for r in caplog.records if "request_data" in r.message]
    response_logs = [r.message for r in caplog.records if "response_data" in r.message]
    assert any("/api/auth/slider-captcha/create" in item for item in request_logs)
    assert all("/api/auth/slider-captcha/create" not in item for item in response_logs)


def test_request_response_body_should_be_disabled_by_default(caplog, monkeypatch):
    monkeypatch.setattr("app.core.request_logging.settings.LOG_REQUEST_BODY_ENABLED", False)
    monkeypatch.setattr("app.core.request_logging.settings.LOG_RESPONSE_BODY_ENABLED", False)
    caplog.set_level(logging.INFO)
    client = TestClient(_build_app())

    response = client.post(
        "/echo",
        json={"phone": "13800000000", "sms_code": "123456"},
        headers={"Authorization": "Bearer secret-token", "x-test-header": "demo"},
    )
    assert response.status_code == 200

    request_logs = [r.message for r in caplog.records if "request_data" in r.message]
    response_logs = [r.message for r in caplog.records if "response_data" in r.message]
    assert request_logs
    assert response_logs
    assert "123456" not in request_logs[-1]
    assert "secret-token" not in request_logs[-1]
    assert "x-test-header" not in request_logs[-1]
    assert "13800000000" not in request_logs[-1]
    assert "body=[DISABLED]" in request_logs[-1]
    assert "body=[DISABLED]" in response_logs[-1]
