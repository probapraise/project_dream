import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from project_dream.eval_suite import find_latest_run
from project_dream.storage import persist_eval as persist_eval_file
from project_dream.storage import persist_run as persist_run_file


def _coerce_non_negative_int(value: object, *, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(0, parsed)


def _extract_stage_trace_from_graph_node_trace(graph_node_trace: dict) -> dict:
    stage_retry_count = 0
    stage_failure_count = 0
    max_stage_attempts = 0

    node_attempts = graph_node_trace.get("node_attempts", {})
    if isinstance(node_attempts, dict):
        for raw_attempts in node_attempts.values():
            max_stage_attempts = max(
                max_stage_attempts,
                _coerce_non_negative_int(raw_attempts, default=0),
            )

    stage_checkpoints = graph_node_trace.get("stage_checkpoints", [])
    if isinstance(stage_checkpoints, list):
        for row in stage_checkpoints:
            if not isinstance(row, dict):
                continue
            outcome = str(row.get("outcome", ""))
            if outcome == "retry":
                stage_retry_count += 1
            elif outcome == "failed":
                stage_failure_count += 1
            max_stage_attempts = max(
                max_stage_attempts,
                _coerce_non_negative_int(row.get("attempt"), default=0),
            )

    nodes = graph_node_trace.get("nodes", [])
    if max_stage_attempts <= 0 and isinstance(nodes, list) and nodes:
        max_stage_attempts = 1

    return {
        "stage_retry_count": stage_retry_count,
        "stage_failure_count": stage_failure_count,
        "max_stage_attempts": max_stage_attempts,
    }


def _extract_stage_trace_from_runlog_rows(rows: list[dict]) -> dict:
    stage_retry_count = 0
    stage_failure_count = 0
    max_stage_attempts = 0
    saw_graph_node = False

    for row in rows:
        if not isinstance(row, dict):
            continue
        row_type = str(row.get("type", ""))
        if row_type == "graph_node":
            saw_graph_node = True
            continue
        if row_type == "graph_node_attempt":
            max_stage_attempts = max(
                max_stage_attempts,
                _coerce_non_negative_int(row.get("attempts"), default=0),
            )
            continue
        if row_type == "stage_checkpoint":
            outcome = str(row.get("outcome", ""))
            if outcome == "retry":
                stage_retry_count += 1
            elif outcome == "failed":
                stage_failure_count += 1
            max_stage_attempts = max(
                max_stage_attempts,
                _coerce_non_negative_int(row.get("attempt"), default=0),
            )

    if max_stage_attempts <= 0 and saw_graph_node:
        max_stage_attempts = 1

    return {
        "stage_retry_count": stage_retry_count,
        "stage_failure_count": stage_failure_count,
        "max_stage_attempts": max_stage_attempts,
    }


def _build_runlog_summary(rows: list[dict]) -> dict:
    row_counts: dict[str, int] = {}
    for row in rows:
        row_type = str(row.get("type", "")).strip() if isinstance(row, dict) else ""
        key = row_type or "unknown"
        row_counts[key] = row_counts.get(key, 0) + 1

    stage_trace = _extract_stage_trace_from_runlog_rows(rows)
    return {
        "row_counts": row_counts,
        "stage": {
            "retry_count": int(stage_trace["stage_retry_count"]),
            "failure_count": int(stage_trace["stage_failure_count"]),
            "max_attempts": int(stage_trace["max_stage_attempts"]),
        },
    }


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

    def list_runs(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        seed_id: str | None = None,
        board_id: str | None = None,
        status: str | None = None,
        pack_fingerprint: str | None = None,
    ) -> dict:
        ...

    def load_report(self, run_id: str) -> dict:
        ...

    def load_eval(self, run_id: str) -> dict:
        ...

    def load_runlog(self, run_id: str) -> dict:
        ...

    def persist_regression_summary(self, summary: dict) -> None:
        ...

    def load_latest_regression_summary(self) -> dict:
        ...

    def load_regression_summary(self, summary_id: str) -> dict:
        ...

    def list_regression_summaries(
        self,
        limit: int | None = None,
        offset: int = 0,
        metric_set: str | None = None,
        pass_fail: bool | None = None,
    ) -> dict:
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

    def _validate_list_params(self, *, limit: int, offset: int) -> None:
        if limit < 1:
            raise ValueError(f"Invalid limit: {limit}")
        if offset < 0:
            raise ValueError(f"Invalid offset: {offset}")

    def _list_run_directories(self) -> list[Path]:
        if not self.runs_dir.exists():
            return []

        run_dirs = [path for path in self.runs_dir.glob("run-*") if path.is_dir()]
        run_dirs.sort(key=lambda path: (path.stat().st_mtime, path.name), reverse=True)
        return run_dirs

    def _read_json_if_exists(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _extract_run_file_metadata(self, run_dir: Path) -> dict:
        report = self._read_json_if_exists(run_dir / "report.json")
        eval_payload = self._read_json_if_exists(run_dir / "eval.json")
        runlog_path = run_dir / "runlog.jsonl"

        board_id = ""
        zone_id = ""
        status = ""
        termination_reason = ""
        total_reports = 0
        pack_fingerprint = ""
        runlog_rows: list[dict] = []

        if runlog_path.exists():
            for line in runlog_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                runlog_rows.append(row)
                row_type = str(row.get("type", ""))

                if row_type == "context":
                    bundle = row.get("bundle", {})
                    if isinstance(bundle, dict):
                        if not board_id:
                            board_id = str(bundle.get("board_id", ""))
                        if not zone_id:
                            zone_id = str(bundle.get("zone_id", ""))
                    if not pack_fingerprint:
                        pack_fingerprint = str(row.get("pack_fingerprint", "")).strip()
                elif row_type == "round":
                    if not board_id:
                        board_id = str(row.get("board_id", ""))
                elif row_type == "end_condition":
                    status = str(row.get("status", ""))
                    termination_reason = str(row.get("termination_reason", ""))
                elif row_type == "moderation_decision":
                    if not status:
                        status = str(row.get("status_after", ""))
                    total_reports = max(
                        total_reports,
                        _coerce_non_negative_int(row.get("report_total"), default=0),
                    )

        stage_trace = _extract_stage_trace_from_runlog_rows(runlog_rows)

        created_at = datetime.fromtimestamp(run_dir.stat().st_mtime, tz=UTC).isoformat()
        report_gate = report.get("report_gate", {}) if isinstance(report, dict) else {}
        report_gate_pass = (
            bool(report_gate.get("pass_fail"))
            if isinstance(report_gate, dict) and "pass_fail" in report_gate
            else None
        )
        eval_pass = bool(eval_payload.get("pass_fail")) if "pass_fail" in eval_payload else None

        return {
            "run_id": run_dir.name,
            "run_dir": str(run_dir),
            "created_at_utc": created_at,
            "seed_id": str(report.get("seed_id", "")) if isinstance(report, dict) else "",
            "board_id": board_id,
            "zone_id": zone_id,
            "status": status,
            "termination_reason": termination_reason,
            "total_reports": total_reports,
            "pack_fingerprint": pack_fingerprint,
            "stage_retry_count": stage_trace["stage_retry_count"],
            "stage_failure_count": stage_trace["stage_failure_count"],
            "max_stage_attempts": stage_trace["max_stage_attempts"],
            "report_gate_pass": report_gate_pass,
            "eval_pass": eval_pass,
        }

    def list_runs(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        seed_id: str | None = None,
        board_id: str | None = None,
        status: str | None = None,
        pack_fingerprint: str | None = None,
    ) -> dict:
        self._validate_list_params(limit=limit, offset=offset)

        rows = [self._extract_run_file_metadata(run_dir) for run_dir in self._list_run_directories()]
        if seed_id:
            rows = [row for row in rows if row.get("seed_id", "") == seed_id]
        if board_id:
            rows = [row for row in rows if row.get("board_id", "") == board_id]
        if status:
            rows = [row for row in rows if row.get("status", "") == status]
        if pack_fingerprint:
            rows = [row for row in rows if row.get("pack_fingerprint", "") == pack_fingerprint]

        total = len(rows)
        items = rows[offset : offset + limit]
        return {
            "count": len(items),
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items,
        }

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
        return {"run_id": run_id, "rows": rows, "summary": _build_runlog_summary(rows)}

    def persist_regression_summary(self, summary: dict) -> None:
        # File backend keeps regression metadata as files only.
        return None

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

    def list_regression_summaries(
        self,
        limit: int | None = None,
        offset: int = 0,
        metric_set: str | None = None,
        pass_fail: bool | None = None,
    ) -> dict:
        if limit is not None and limit < 1:
            raise ValueError(f"Invalid limit: {limit}")
        if offset < 0:
            raise ValueError(f"Invalid offset: {offset}")

        regressions_dir = self.runs_dir / "regressions"
        summary_files = sorted(regressions_dir.glob("regression-*.json"), reverse=True)

        rows: list[dict] = []
        for path in summary_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            totals = payload.get("totals", {})
            row = {
                "summary_id": path.name,
                "summary_path": str(path),
                "generated_at_utc": payload.get("generated_at_utc"),
                "metric_set": payload.get("metric_set"),
                "pass_fail": bool(payload.get("pass_fail")),
                "seed_runs": int(totals.get("seed_runs", 0)),
            }
            rows.append(row)

        if metric_set is not None:
            rows = [row for row in rows if str(row.get("metric_set", "")) == metric_set]
        if pass_fail is not None:
            rows = [row for row in rows if bool(row.get("pass_fail")) is bool(pass_fail)]

        total = len(rows)
        if limit is None:
            items = rows[offset:]
        else:
            items = rows[offset : offset + limit]

        return {
            "count": len(items),
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items,
        }


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
                    pack_fingerprint TEXT DEFAULT '',
                    stage_retry_count INTEGER DEFAULT 0,
                    stage_failure_count INTEGER DEFAULT 0,
                    max_stage_attempts INTEGER DEFAULT 0,
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS regression_summaries (
                    summary_id TEXT PRIMARY KEY,
                    summary_path TEXT NOT NULL,
                    generated_at_utc TEXT,
                    metric_set TEXT,
                    pass_fail INTEGER,
                    seed_runs INTEGER DEFAULT 0,
                    payload_json TEXT NOT NULL,
                    indexed_at_utc TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_regression_summaries_generated_at
                ON regression_summaries (generated_at_utc DESC)
                """
            )
            columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(runs)").fetchall()}
            if "stage_retry_count" not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN stage_retry_count INTEGER DEFAULT 0")
            if "stage_failure_count" not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN stage_failure_count INTEGER DEFAULT 0")
            if "max_stage_attempts" not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN max_stage_attempts INTEGER DEFAULT 0")
            if "pack_fingerprint" not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN pack_fingerprint TEXT DEFAULT ''")
            conn.commit()

    def _upsert_run_index(self, run_dir: Path, sim_result: dict, report: dict) -> None:
        thread_state = sim_result.get("thread_state", {}) if isinstance(sim_result, dict) else {}
        report_gate = report.get("report_gate", {}) if isinstance(report, dict) else {}
        graph_node_trace = sim_result.get("graph_node_trace", {}) if isinstance(sim_result, dict) else {}
        stage_trace = (
            _extract_stage_trace_from_graph_node_trace(graph_node_trace)
            if isinstance(graph_node_trace, dict)
            else {"stage_retry_count": 0, "stage_failure_count": 0, "max_stage_attempts": 0}
        )
        pack_fingerprint = str(sim_result.get("pack_fingerprint", "")).strip()
        created_at_utc = datetime.now(UTC).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, run_dir, created_at_utc, seed_id, board_id, zone_id, status,
                    termination_reason, total_reports, pack_fingerprint, stage_retry_count, stage_failure_count,
                    max_stage_attempts, report_gate_pass, eval_pass
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    run_dir=excluded.run_dir,
                    created_at_utc=excluded.created_at_utc,
                    seed_id=excluded.seed_id,
                    board_id=excluded.board_id,
                    zone_id=excluded.zone_id,
                    status=excluded.status,
                    termination_reason=excluded.termination_reason,
                    total_reports=excluded.total_reports,
                    pack_fingerprint=excluded.pack_fingerprint,
                    stage_retry_count=excluded.stage_retry_count,
                    stage_failure_count=excluded.stage_failure_count,
                    max_stage_attempts=excluded.max_stage_attempts,
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
                    pack_fingerprint,
                    int(stage_trace["stage_retry_count"]),
                    int(stage_trace["stage_failure_count"]),
                    int(stage_trace["max_stage_attempts"]),
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

    def list_runs(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        seed_id: str | None = None,
        board_id: str | None = None,
        status: str | None = None,
        pack_fingerprint: str | None = None,
    ) -> dict:
        if limit < 1:
            raise ValueError(f"Invalid limit: {limit}")
        if offset < 0:
            raise ValueError(f"Invalid offset: {offset}")

        clauses: list[str] = []
        params: list[object] = []
        if seed_id:
            clauses.append("seed_id = ?")
            params.append(seed_id)
        if board_id:
            clauses.append("board_id = ?")
            params.append(board_id)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if pack_fingerprint:
            clauses.append("pack_fingerprint = ?")
            params.append(pack_fingerprint)
        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as conn:
            total_row = conn.execute(
                f"SELECT COUNT(*) AS total FROM runs {where_clause}",
                params,
            ).fetchone()
            total = int(total_row["total"]) if total_row is not None else 0

            rows = conn.execute(
                f"""
                SELECT run_id, run_dir, created_at_utc, seed_id, board_id, zone_id, status,
                       termination_reason, total_reports, pack_fingerprint, stage_retry_count, stage_failure_count,
                       max_stage_attempts, report_gate_pass, eval_pass
                FROM runs
                {where_clause}
                ORDER BY created_at_utc DESC
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()

        items: list[dict] = []
        for row in rows:
            report_gate_raw = row["report_gate_pass"]
            eval_pass_raw = row["eval_pass"]
            items.append(
                {
                    "run_id": str(row["run_id"]),
                    "run_dir": str(row["run_dir"]),
                    "created_at_utc": str(row["created_at_utc"]),
                    "seed_id": str(row["seed_id"] or ""),
                    "board_id": str(row["board_id"] or ""),
                    "zone_id": str(row["zone_id"] or ""),
                    "status": str(row["status"] or ""),
                    "termination_reason": str(row["termination_reason"] or ""),
                    "total_reports": int(row["total_reports"] or 0),
                    "pack_fingerprint": str(row["pack_fingerprint"] or ""),
                    "stage_retry_count": int(row["stage_retry_count"] or 0),
                    "stage_failure_count": int(row["stage_failure_count"] or 0),
                    "max_stage_attempts": int(row["max_stage_attempts"] or 0),
                    "report_gate_pass": (
                        bool(int(report_gate_raw)) if report_gate_raw is not None else None
                    ),
                    "eval_pass": bool(int(eval_pass_raw)) if eval_pass_raw is not None else None,
                }
            )

        return {
            "count": len(items),
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items,
        }

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
        return {"run_id": run_id, "rows": rows, "summary": _build_runlog_summary(rows)}

    def _sync_regression_indexes_from_files(self) -> None:
        regressions_dir = self.runs_dir / "regressions"
        if not regressions_dir.exists():
            return

        for path in sorted(regressions_dir.glob("regression-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            payload.setdefault("summary_path", str(path))
            self.persist_regression_summary(payload)

    def persist_regression_summary(self, summary: dict) -> None:
        summary_path_value = str(summary.get("summary_path", "")).strip()
        if summary_path_value:
            summary_path = Path(summary_path_value)
        else:
            generated = datetime.now(UTC).strftime("regression-%Y%m%d-%H%M%S-%f.json")
            summary_path = self.runs_dir / "regressions" / generated

        summary_id = summary_path.name
        payload = dict(summary)
        payload.setdefault("summary_path", str(summary_path))
        totals = payload.get("totals", {})
        generated_at_utc = str(payload.get("generated_at_utc", ""))
        metric_set = str(payload.get("metric_set", ""))
        pass_fail = int(bool(payload.get("pass_fail")))
        seed_runs = int(totals.get("seed_runs", 0)) if isinstance(totals, dict) else 0
        payload_json = json.dumps(payload, ensure_ascii=False)
        indexed_at_utc = datetime.now(UTC).isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO regression_summaries (
                    summary_id, summary_path, generated_at_utc, metric_set,
                    pass_fail, seed_runs, payload_json, indexed_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(summary_id) DO UPDATE SET
                    summary_path=excluded.summary_path,
                    generated_at_utc=excluded.generated_at_utc,
                    metric_set=excluded.metric_set,
                    pass_fail=excluded.pass_fail,
                    seed_runs=excluded.seed_runs,
                    payload_json=excluded.payload_json,
                    indexed_at_utc=excluded.indexed_at_utc
                """,
                (
                    summary_id,
                    str(summary_path),
                    generated_at_utc,
                    metric_set,
                    pass_fail,
                    seed_runs,
                    payload_json,
                    indexed_at_utc,
                ),
            )
            conn.commit()

    def _load_indexed_regression_summary(self, summary_filename: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT summary_path, payload_json
                FROM regression_summaries
                WHERE summary_id = ?
                """,
                (summary_filename,),
            ).fetchone()
        if row is None:
            return None

        payload_raw = str(row["payload_json"] or "").strip()
        if not payload_raw:
            return None
        payload = json.loads(payload_raw)
        payload.setdefault("summary_path", str(row["summary_path"]))
        return payload

    def load_latest_regression_summary(self) -> dict:
        self._sync_regression_indexes_from_files()
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT summary_id
                FROM regression_summaries
                ORDER BY COALESCE(generated_at_utc, indexed_at_utc) DESC, summary_id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is not None:
            return self.load_regression_summary(str(row["summary_id"]))

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
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload.setdefault("summary_path", str(path))
            self.persist_regression_summary(payload)
            return payload

        indexed_payload = self._load_indexed_regression_summary(filename)
        if indexed_payload is not None:
            return indexed_payload
        raise FileNotFoundError(f"Regression summary not found: {summary_id}")

    def list_regression_summaries(
        self,
        limit: int | None = None,
        offset: int = 0,
        metric_set: str | None = None,
        pass_fail: bool | None = None,
    ) -> dict:
        if limit is not None and limit < 1:
            raise ValueError(f"Invalid limit: {limit}")
        if offset < 0:
            raise ValueError(f"Invalid offset: {offset}")

        self._sync_regression_indexes_from_files()
        clauses: list[str] = []
        params: list[object] = []
        if metric_set is not None:
            clauses.append("metric_set = ?")
            params.append(metric_set)
        if pass_fail is not None:
            clauses.append("pass_fail = ?")
            params.append(int(bool(pass_fail)))
        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        with self._connect() as conn:
            total_row = conn.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM regression_summaries
                {where_clause}
                """,
                params,
            ).fetchone()
            total = int(total_row["total"]) if total_row is not None else 0

            if limit is None:
                query = f"""
                SELECT summary_id, summary_path, generated_at_utc, metric_set, pass_fail, seed_runs
                FROM regression_summaries
                {where_clause}
                ORDER BY COALESCE(generated_at_utc, indexed_at_utc) DESC, summary_id DESC
                LIMIT -1 OFFSET ?
                """
                rows = conn.execute(query, [*params, offset]).fetchall()
            else:
                query = f"""
                SELECT summary_id, summary_path, generated_at_utc, metric_set, pass_fail, seed_runs
                FROM regression_summaries
                {where_clause}
                ORDER BY COALESCE(generated_at_utc, indexed_at_utc) DESC, summary_id DESC
                LIMIT ? OFFSET ?
                """
                rows = conn.execute(query, [*params, limit, offset]).fetchall()

        if rows:
            items = [
                {
                    "summary_id": str(row["summary_id"]),
                    "summary_path": str(row["summary_path"]),
                    "generated_at_utc": row["generated_at_utc"],
                    "metric_set": row["metric_set"],
                    "pass_fail": bool(int(row["pass_fail"])),
                    "seed_runs": int(row["seed_runs"] or 0),
                }
                for row in rows
            ]
            return {
                "count": len(items),
                "total": total,
                "limit": limit,
                "offset": offset,
                "items": items,
            }

        regressions_dir = self.runs_dir / "regressions"
        summary_files = sorted(regressions_dir.glob("regression-*.json"), reverse=True)

        all_items: list[dict] = []
        for path in summary_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            totals = payload.get("totals", {})
            all_items.append(
                {
                    "summary_id": path.name,
                    "summary_path": str(path),
                    "generated_at_utc": payload.get("generated_at_utc"),
                    "metric_set": payload.get("metric_set"),
                    "pass_fail": bool(payload.get("pass_fail")),
                    "seed_runs": int(totals.get("seed_runs", 0)),
                }
            )

        if metric_set is not None:
            all_items = [item for item in all_items if str(item.get("metric_set", "")) == metric_set]
        if pass_fail is not None:
            all_items = [item for item in all_items if bool(item.get("pass_fail")) is bool(pass_fail)]

        total = len(all_items)
        if limit is None:
            items = all_items[offset:]
        else:
            items = all_items[offset : offset + limit]
        return {
            "count": len(items),
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items,
        }
