"""Regression tests for local CV handling without a running Ollama model."""

import io
import json
import os
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

import main as api


async def _run_direct(function, *args):
    """Keep these unit tests independent of an ASGI test server."""
    return function(*args)


def _run_without_event_loop(coroutine):
    """The stubbed endpoint completes synchronously at every await."""
    try:
        coroutine.send(None)
    except StopIteration as result:
        return result.value
    raise AssertionError("Unexpected asynchronous suspension in the stubbed endpoint")


def _request(name, data, job_description="Python engineer"):
    upload = UploadFile(file=io.BytesIO(data), filename=name)
    return _run_without_event_loop(api.tailor_resume(upload, job_description))


def _stub_pipeline(monkeypatch, output_paths):
    monkeypatch.setattr(api, "run_in_threadpool", _run_direct)
    monkeypatch.setattr(
        api,
        "extract_text_from_file",
        lambda _path: {"success": True, "extracted_text": "Valid CV text. " * 5},
    )
    monkeypatch.setattr(
        api,
        "optimize_resume",
        lambda _cv, _job: SimpleNamespace(model_dump=lambda: {"summary": "Verified by test"}),
    )

    def fake_generate(_data, output_path):
        output_paths.append(output_path)
        with open(output_path, "wb") as output:
            output.write(b"%PDF-1.4 test")

    monkeypatch.setattr(api, "generate_pdf_from_dict", fake_generate)


def test_unique_private_output_and_safe_download_name(monkeypatch):
    output_paths = []
    _stub_pipeline(monkeypatch, output_paths)

    for _ in range(2):
        response = _request("my resume.pdf", b"%PDF-1.4 test")
        assert response.status_code == 200
        body = json.loads(response.body)
        assert body["filename"] == "tailored_my_resume.pdf"
        assert body["pdf_base64"]

    assert output_paths[0] != output_paths[1]
    assert all(not os.path.exists(path) for path in output_paths)
    assert api.safe_download_filename(r"C:\private\résumé.pdf") == "tailored_r_sum.pdf"
    assert api.safe_download_filename("../.pdf") == "tailored_resume.pdf"


def test_upload_limit_rejects_before_parsing(monkeypatch):
    monkeypatch.setattr(api, "MAX_UPLOAD_BYTES", 4)
    monkeypatch.setattr(api, "run_in_threadpool", _run_direct)
    monkeypatch.setattr(
        api,
        "extract_text_from_file",
        lambda _path: (_ for _ in ()).throw(AssertionError("parser should not run")),
    )
    with pytest.raises(HTTPException) as error:
        _request("resume.pdf", b"12345")
    assert error.value.status_code == 413


def test_model_error_does_not_expose_private_details(monkeypatch):
    output_paths = []
    _stub_pipeline(monkeypatch, output_paths)

    def fail_model(_cv, _job):
        raise RuntimeError("private CV contents")

    monkeypatch.setattr(api, "optimize_resume", fail_model)
    with pytest.raises(HTTPException) as error:
        _request("resume.pdf", b"%PDF-1.4 test")
    assert error.value.status_code == 422
    assert "private CV contents" not in str(error.value.detail)


def test_unhandled_error_does_not_expose_private_details():
    response = _run_without_event_loop(
        api.global_exception_handler(None, RuntimeError("private CV contents"))
    )
    assert response.status_code == 500
    assert "private CV contents" not in response.body.decode()


def test_cors_only_allows_local_frontend():
    cors = next(m for m in api.app.user_middleware if m.cls is api.CORSMiddleware)
    assert cors.kwargs["allow_origins"] == [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]
    assert cors.kwargs["allow_credentials"] is False


def test_api_requires_cv_and_nonblank_job_description():
    """A direct API caller must supply the same two inputs as the UI."""
    route = next(route for route in api.app.routes if route.path == "/api/v1/tailor")
    body_params = {param.name: param for param in route.dependant.body_params}
    assert body_params["file"].required
    assert body_params["job_description"].required

    with pytest.raises(HTTPException) as error:
        _request("resume.pdf", b"%PDF-1.4 test", "   ")
    assert error.value.status_code == 400
