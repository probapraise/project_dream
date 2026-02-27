import os
import subprocess
import sys
from pathlib import Path


def test_python_m_cli_executes_simulation(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent
    seed_path = repo_root / "examples" / "seeds" / "seed_001.json"
    output_dir = tmp_path / "runs"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(repo_root / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "project_dream.cli",
            "simulate",
            "--seed",
            str(seed_path),
            "--output-dir",
            str(output_dir),
            "--rounds",
            "3",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert any(output_dir.glob("*/runlog.jsonl"))
