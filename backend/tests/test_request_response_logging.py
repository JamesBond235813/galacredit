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

    return app


def test_request_response_log_contains_trace_id_and_url(caplog):
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


def test_upload_and_download_content_should_be_masked(caplog):
    caplog.set_level(logging.INFO)
    client = TestClient(_build_app())

    upload_response = client.post("/upload", files={"file": ("a.txt", b"abc", "text/plain")})
    assert upload_response.status_code == 200

    download_response = client.get("/download")
    assert download_response.status_code == 200

    request_logs = [r.message for r in caplog.records if "request_data" in r.message]
    response_logs = [r.message for r in caplog.records if "response_data" in r.message]
    assert any("[upload file content]" in m for m in request_logs)
    assert any("[download file content]" in m for m in response_logs)
