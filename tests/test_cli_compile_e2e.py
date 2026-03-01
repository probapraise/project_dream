import json
import shutil
from pathlib import Path

from project_dream.cli import main
from project_dream.pack_service import load_packs


def _copy_packs(tmp_path: Path) -> Path:
    dst = tmp_path / "packs"
    shutil.copytree(Path("packs"), dst)
    return dst


def test_cli_compile_writes_world_pack_and_manifest(tmp_path: Path):
    packs_dir = _copy_packs(tmp_path)
    authoring_dir = tmp_path / "authoring"
    authoring_dir.mkdir(parents=True, exist_ok=True)

    payload = json.loads((packs_dir / "world_pack.json").read_text(encoding="utf-8"))
    payload["version"] = "9.9.9"
    payload["forbidden_terms"] = ["인장 위조법", "실명 주소"]
    (authoring_dir / "world_pack.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    rc = main(
        [
            "compile",
            "--authoring-dir",
            str(authoring_dir),
            "--packs-dir",
            str(packs_dir),
        ]
    )

    assert rc == 0
    compiled = json.loads((packs_dir / "world_pack.json").read_text(encoding="utf-8"))
    assert compiled["version"] == "9.9.9"
    assert compiled["forbidden_terms"] == ["인장 위조법", "실명 주소"]

    manifest = json.loads((packs_dir / "pack_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "pack_manifest.v1"
    assert "world_pack.json" in manifest["files"]

    loaded = load_packs(packs_dir)
    assert loaded.world_schema["version"] == "9.9.9"
