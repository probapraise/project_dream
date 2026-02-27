from pathlib import Path
import json
from typing import Protocol

from project_dream.eval_suite import find_latest_run
from project_dream.storage import persist_eval, persist_run


class RunRepository(Protocol):
    runs_dir: Path

    def persist_run(self, sim_result: dict, report: dict) -> Path:
        ...

    def persist_eval(self, run_dir: Path, eval_result: dict) -> Path:
        ...

    def find_latest_run(self) -> Path:
        ...

    def get_run(self, run_id: str) -> Path:
        ...

    def load_report(self, run_id: str) -> dict:
        ...

    def load_eval(self, run_id: str) -> dict:
        ...

    def load_runlog(self, run_id: str) -> dict:
        ...

    def load_latest_regression_summary(self) -> dict:
        ...


class FileRunRepository:
    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir

    def persist_run(self, sim_result: dict, report: dict) -> Path:
        return persist_run(self.runs_dir, sim_result, report)

    def persist_eval(self, run_dir: Path, eval_result: dict) -> Path:
        return persist_eval(run_dir, eval_result)

    def find_latest_run(self) -> Path:
        return find_latest_run(self.runs_dir)

    def get_run(self, run_id: str) -> Path:
        run_dir = self.runs_dir / run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Run not found: {run_id}")
        return run_dir

    def load_report(self, run_id: str) -> dict:
        run_dir = self.get_run(run_id)
        path = run_dir / "report.json"
        if not path.exists():
            raise FileNotFoundError(f"Report not found for run: {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def load_eval(self, run_id: str) -> dict:
        run_dir = self.get_run(run_id)
        path = run_dir / "eval.json"
        if not path.exists():
            raise FileNotFoundError(f"Eval not found for run: {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def load_runlog(self, run_id: str) -> dict:
        run_dir = self.get_run(run_id)
        path = run_dir / "runlog.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"Runlog not found for run: {run_id}")
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rows.append(json.loads(line))
        return {"run_id": run_id, "rows": rows}

    def load_latest_regression_summary(self) -> dict:
        regressions_dir = self.runs_dir / "regressions"
        summary_files = sorted(regressions_dir.glob("regression-*.json"))
        if not summary_files:
            raise FileNotFoundError(f"No regression summary found under {regressions_dir}")

        latest = summary_files[-1]
        payload = json.loads(latest.read_text(encoding="utf-8"))
        payload.setdefault("summary_path", str(latest))
        return payload
