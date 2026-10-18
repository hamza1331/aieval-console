"""Tests for SPA static asset serving and root health endpoints."""

from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app


def test_root_health_endpoint():
    """Verify that GET /health returns 200 and matches HealthResponse schema."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "app_version" in data
    assert "aieval_version" in data


def test_spa_serving_and_fallback(monkeypatch):
    """Verify SPA serves index.html at root and on unknown non-API routes."""
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        index_file = tmp_path / "index.html"
        index_file.write_text("<!DOCTYPE html><html><body><div id='root'>SPA</div></body></html>")

        assets_dir = tmp_path / "assets"
        assets_dir.mkdir()
        dummy_asset = assets_dir / "main.js"
        dummy_asset.write_text("console.log('test asset');")

        monkeypatch.setattr(settings, "STATIC_DIR", str(tmp_path))
        app = create_app()
        client = TestClient(app)

        # 1. Root route returns index.html
        res_root = client.get("/")
        assert res_root.status_code == 200
        assert "<div id='root'>SPA</div>" in res_root.text

        # 2. Deep frontend route returns index.html (SPA client routing)
        res_deep = client.get("/contracts/abc-123")
        assert res_deep.status_code == 200
        assert "<div id='root'>SPA</div>" in res_deep.text

        # 3. Static asset route returns the asset
        res_asset = client.get("/assets/main.js")
        assert res_asset.status_code == 200
        assert "console.log('test asset');" in res_asset.text

        # 4. Unknown API route does not fallback to HTML; returns 404 JSON
        res_api = client.get("/api/v1/non_existent_endpoint")
        assert res_api.status_code == 404
        assert res_api.headers.get("content-type", "").startswith("application/json")
