from pathlib import Path
import json
import sqlite3
from datetime import UTC, datetime
from typing import Protocol

from project_dream.eval_suite import find_latest_run
from project_dream.storage import persist_eval as persist_eval_file
from project_dream.storage import persist_run as persist_run_file


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

    def load_regression_summary(self, summary_id: str) -> dict:
        ...

    def list_regression_summaries(self, limit: int | None = None) -> dict:
        ...


class FileRunRepository:
    def __init__(self, runs_dir: Path):
        self.runs_dir = runs_dir

    def persist_run(self, sim_result: dict, report: dict) -> Path:
        return persist_run_file(self.runs_dir, sim_result, report)

    def persist_eval(self, run_dir: Path, eval_result: dict) -> Path:
        return persist_eval_file(run_dir, eval_result)

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
        return self.load_regression_summary(latest.name)

    def load_regression_summary(self, summary_id: str) -> dict:
        if "/" in summary_id or "\\" in summary_id:
            raise ValueError(f"Invalid summary id: {summary_id}")

        filename = summary_id if summary_id.endswith(".json") else f"{summary_id}.json"
        path = self.runs_dir / "regressions" / filename
        if not path.exists():
            raise FileNotFoundError(f"Regression summary not found: {summary_id}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.setdefault("summary_path", str(path))
        return payload

    def list_regression_summaries(self, limit: int | None = None) -> dict:
        if limit is not None and limit < 1:
            raise ValueError(f"Invalid limit: {limit}")

        regressions_dir = self.runs_dir / "regressions"
        summary_files = sorted(regressions_dir.glob("regression-*.json"), reverse=True)
        if limit is not None:
            summary_files = summary_files[:limit]

        items = []
        for path in summary_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            totals = payload.get("totals", {})
            items.append(
                {
                    "summary_id": path.name,
                    "summary_path": str(path),
                    "generated_at_utc": payload.get("generated_at_utc"),
                    "metric_set": payload.get("metric_set"),
                    "pass_fail": bool(payload.get("pass_fail")),
                    "seed_runs": int(totals.get("seed_runs", 0)),
                }
            )

        return {"count": len(items), "items": items}


class SQLiteRunRepository:
    def __init__(self, runs_dir: Path, db_path: Path | None = None):
        self.runs_dir = runs_dir
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or (self.runs_dir / "runs.sqlite3")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    run_dir TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    seed_id TEXT,
                    board_id TEXT,
                    zone_id TEXT,
                    status TEXT,
                    termination_reason TEXT,
                    total_reports INTEGER DEFAULT 0,
                    report_gate_pass INTEGER,
                    eval_pass INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_runs_created_at
                ON runs (created_at_utc DESC)
                """
            )
            conn.commit()

    def _upsert_run_index(self, run_dir: Path, sim_result: dict, report: dict) -> None:
        thread_state = sim_result.get("thread_state", {}) if isinstance(sim_result, dict) else {}
        report_gate = report.get("report_gate", {}) if isinstance(report, dict) else {}
        created_at_utc = datetime.now(UTC).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, run_dir, created_at_utc, seed_id, board_id, zone_id, status,
                    termination_reason, total_reports, report_gate_pass, eval_pass
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    run_dir=excluded.run_dir,
                    created_at_utc=excluded.created_at_utc,
                    seed_id=excluded.seed_id,
                    board_id=excluded.board_id,
                    zone_id=excluded.zone_id,
                    status=excluded.status,
                    termination_reason=excluded.termination_reason,
                    total_reports=excluded.total_reports,
                    report_gate_pass=excluded.report_gate_pass
                """,
                (
                    run_dir.name,
                    str(run_dir),
                    created_at_utc,
                    str(report.get("seed_id", "")) if isinstance(report, dict) else "",
                    str(thread_state.get("board_id", "")),
                    str(thread_state.get("zone_id", "")),
                    str(thread_state.get("status", "")),
                    str(thread_state.get("termination_reason", "")),
                    int(thread_state.get("total_reports", 0)),
                    int(bool(report_gate.get("pass_fail"))) if isinstance(report_gate, dict) else 0,
                    None,
                ),
            )
            conn.commit()

    def _set_eval_status(self, run_id: str, eval_result: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET eval_pass = ? WHERE run_id = ?",
                (int(bool(eval_result.get("pass_fail"))), run_id),
            )
            conn.commit()

    def _get_indexed_run_dir(self, run_id: str) -> Path | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT run_dir FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            return None
        run_dir = Path(str(row["run_dir"]))
        if run_dir.exists():
            return run_dir
        fallback = self.runs_dir / run_id
        if fallback.exists():
            return fallback
        return None

    def persist_run(self, sim_result: dict, report: dict) -> Path:
        run_dir = persist_run_file(self.runs_dir, sim_result, report)
        self._upsert_run_index(run_dir, sim_result, report)
        return run_dir

    def persist_eval(self, run_dir: Path, eval_result: dict) -> Path:
        output = persist_eval_file(run_dir, eval_result)
        self._set_eval_status(run_dir.name, eval_result)
        return output

    def find_latest_run(self) -> Path:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT run_id, run_dir FROM runs ORDER BY created_at_utc DESC LIMIT 1"
            ).fetchone()
        if row is not None:
            run_dir = Path(str(row["run_dir"]))
            if run_dir.exists():
                return run_dir
            fallback = self.runs_dir / str(row["run_id"])
            if fallback.exists():
                return fallback
        return find_latest_run(self.runs_dir)

    def get_run(self, run_id: str) -> Path:
        indexed = self._get_indexed_run_dir(run_id)
        if indexed is not None:
            return indexed
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
        return self.load_regression_summary(latest.name)

    def load_regression_summary(self, summary_id: str) -> dict:
        if "/" in summary_id or "\\" in summary_id:
            raise ValueError(f"Invalid summary id: {summary_id}")

        filename = summary_id if summary_id.endswith(".json") else f"{summary_id}.json"
        path = self.runs_dir / "regressions" / filename
        if not path.exists():
            raise FileNotFoundError(f"Regression summary not found: {summary_id}")

        payload = json.loads(path.read_text(encoding="utf-8"))
        payload.setdefault("summary_path", str(path))
        return payload

    def list_regression_summaries(self, limit: int | None = None) -> dict:
        if limit is not None and limit < 1:
            raise ValueError(f"Invalid limit: {limit}")

        regressions_dir = self.runs_dir / "regressions"
        summary_files = sorted(regressions_dir.glob("regression-*.json"), reverse=True)
        if limit is not None:
            summary_files = summary_files[:limit]

        items = []
        for path in summary_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            totals = payload.get("totals", {})
            items.append(
                {
                    "summary_id": path.name,
                    "summary_path": str(path),
                    "generated_at_utc": payload.get("generated_at_utc"),
                    "metric_set": payload.get("metric_set"),
                    "pass_fail": bool(payload.get("pass_fail")),
                    "seed_runs": int(totals.get("seed_runs", 0)),
                }
            )

        return {"count": len(items), "items": items}
