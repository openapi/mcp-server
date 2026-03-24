from pathlib import Path

import pytest

from openapi_mcp_sdk import storage_backend


def test_save_and_read_file_with_local_backend(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_STORAGE_BACKEND", "local")
    monkeypatch.setenv("MCP_STORAGE_PATH", str(tmp_path))

    storage_backend.save_file("nested/file.txt", b"hello", "text/plain")

    content, content_type = storage_backend.read_file("nested/file.txt")

    assert content == b"hello"
    assert content_type == "application/octet-stream"
    assert (tmp_path / "nested" / "file.txt").read_bytes() == b"hello"


def test_read_file_raises_for_missing_local_file(tmp_path, monkeypatch):
    monkeypatch.setenv("MCP_STORAGE_BACKEND", "local")
    monkeypatch.setenv("MCP_STORAGE_PATH", str(tmp_path))

    with pytest.raises(FileNotFoundError):
        storage_backend.read_file("missing.txt")


def test_cloud_backends_require_bucket(monkeypatch):
    monkeypatch.setenv("MCP_STORAGE_BACKEND", "gcs")
    monkeypatch.delenv("MCP_STORAGE_BUCKET", raising=False)

    with pytest.raises(RuntimeError, match="MCP_STORAGE_BUCKET"):
        storage_backend._storage_bucket()


def test_storage_path_uses_mcp_storage_path(monkeypatch, tmp_path):
    monkeypatch.setenv("MCP_STORAGE_PATH", str(tmp_path))

    assert storage_backend._storage_path() == Path(tmp_path)
