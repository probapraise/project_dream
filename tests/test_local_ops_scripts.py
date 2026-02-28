from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _script_text(name: str) -> str:
    return (ROOT / "scripts" / name).read_text(encoding="utf-8")


def test_dev_serve_supports_vector_flags_from_env():
    text = _script_text("dev_serve.sh")
    assert "PROJECT_DREAM_VECTOR_BACKEND" in text
    assert "PROJECT_DREAM_VECTOR_DB_PATH" in text
    assert "--vector-backend" in text
    assert "--vector-db-path" in text


def test_regress_live_supports_vector_flags_from_env():
    text = _script_text("regress_live.sh")
    assert "PROJECT_DREAM_LIVE_VECTOR_BACKEND" in text
    assert "PROJECT_DREAM_LIVE_VECTOR_DB_PATH" in text
    assert "--vector-backend" in text
    assert "--vector-db-path" in text


def test_smoke_api_includes_optional_sqlite_vector_check():
    text = _script_text("smoke_api.sh")
    assert "PROJECT_DREAM_SMOKE_VECTOR_SQLITE_CHECK" in text
    assert "PROJECT_DREAM_SMOKE_VECTOR_DB_PATH" in text
    assert "vector_backend" in text
    assert "vector_db_path" in text
    assert "smoke sqlite vector mode" in text
