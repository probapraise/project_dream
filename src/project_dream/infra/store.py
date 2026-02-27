from pathlib import Path
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
