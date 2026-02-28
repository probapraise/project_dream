from pathlib import Path

from project_dream.app_service import evaluate_and_persist, regress_and_persist, simulate_and_persist
from project_dream.kb_index import build_index, get_pack_item as kb_get_pack_item, retrieve_context, search
from project_dream.infra.store import FileRunRepository, RunRepository, SQLiteRunRepository
from project_dream.models import SeedInput
from project_dream.pack_service import load_packs


def _normalize_vector_backend(backend: str) -> str:
    normalized = backend.strip().lower()
    if normalized not in {"memory", "sqlite"}:
        raise ValueError(f"Unknown vector backend: {backend}")
    return normalized


class ProjectDreamAPI:
    def __init__(
        self,
        repository: RunRepository,
        packs_dir: Path,
        corpus_dir: Path = Path("corpus"),
        *,
        vector_backend: str = "memory",
        vector_db_path: Path | None = None,
    ):
        self.repository = repository
        self.packs_dir = packs_dir
        self.corpus_dir = corpus_dir
        self.vector_backend = _normalize_vector_backend(vector_backend)
        self.vector_db_path = vector_db_path

    @classmethod
    def for_local_filesystem(
        cls,
        *,
        runs_dir: Path = Path("runs"),
        packs_dir: Path = Path("packs"),
        corpus_dir: Path = Path("corpus"),
        repository_backend: str = "file",
        sqlite_db_path: Path | None = None,
        vector_backend: str = "memory",
        vector_db_path: Path | None = None,
    ) -> "ProjectDreamAPI":
        backend = repository_backend.strip().lower()
        if backend == "sqlite":
            repository: RunRepository = SQLiteRunRepository(runs_dir, db_path=sqlite_db_path)
        elif backend == "file":
            repository = FileRunRepository(runs_dir)
        else:
            raise ValueError(f"Unknown repository backend: {repository_backend}")
        return cls(
            repository=repository,
            packs_dir=packs_dir,
            corpus_dir=corpus_dir,
            vector_backend=vector_backend,
            vector_db_path=vector_db_path,
        )

    def health(self) -> dict:
        return {"status": "ok", "service": "project-dream"}

    def simulate(
        self,
        seed_payload: dict,
        rounds: int = 3,
        orchestrator_backend: str = "manual",
        vector_backend: str | None = None,
        vector_db_path: Path | None = None,
    ) -> dict:
        seed = SeedInput.model_validate(seed_payload)
        resolved_vector_backend = (
            self.vector_backend
            if vector_backend is None
            else _normalize_vector_backend(vector_backend)
        )
        resolved_vector_db_path = self.vector_db_path if vector_db_path is None else vector_db_path
        run_dir = simulate_and_persist(
            seed,
            rounds=rounds,
            packs_dir=self.packs_dir,
            corpus_dir=self.corpus_dir,
            repository=self.repository,
            orchestrator_backend=orchestrator_backend,
            vector_backend=resolved_vector_backend,
            vector_db_path=resolved_vector_db_path,
        )
        return {"run_id": run_dir.name, "run_dir": str(run_dir)}

    def evaluate(self, run_id: str | None = None, metric_set: str = "v1") -> dict:
        return evaluate_and_persist(
            repository=self.repository,
            run_id=run_id,
            metric_set=metric_set,
        )

    def latest_run(self) -> dict:
        run_dir = self.repository.find_latest_run()
        return {"run_id": run_dir.name, "run_dir": str(run_dir)}

    def list_runs(
        self,
        *,
        limit: int = 20,
        offset: int = 0,
        seed_id: str | None = None,
        board_id: str | None = None,
        status: str | None = None,
    ) -> dict:
        return self.repository.list_runs(
            limit=limit,
            offset=offset,
            seed_id=seed_id,
            board_id=board_id,
            status=status,
        )

    def get_report(self, run_id: str) -> dict:
        return self.repository.load_report(run_id)

    def get_eval(self, run_id: str) -> dict:
        return self.repository.load_eval(run_id)

    def get_runlog(self, run_id: str) -> dict:
        return self.repository.load_runlog(run_id)

    def latest_regression_summary(self) -> dict:
        return self.repository.load_latest_regression_summary()

    def get_regression_summary(self, summary_id: str) -> dict:
        return self.repository.load_regression_summary(summary_id)

    def list_regression_summaries(
        self,
        limit: int | None = None,
        offset: int = 0,
        metric_set: str | None = None,
        pass_fail: bool | None = None,
    ) -> dict:
        return self.repository.list_regression_summaries(
            limit=limit,
            offset=offset,
            metric_set=metric_set,
            pass_fail=pass_fail,
        )

    def regress(
        self,
        *,
        seeds_dir: Path = Path("examples/seeds/regression"),
        rounds: int = 4,
        max_seeds: int = 10,
        metric_set: str = "v1",
        min_community_coverage: int = 2,
        min_conflict_frame_runs: int = 2,
        min_moderation_hook_runs: int = 1,
        min_validation_warning_runs: int = 1,
        orchestrator_backend: str = "manual",
        vector_backend: str | None = None,
        vector_db_path: Path | None = None,
    ) -> dict:
        resolved_vector_backend = (
            self.vector_backend
            if vector_backend is None
            else _normalize_vector_backend(vector_backend)
        )
        resolved_vector_db_path = self.vector_db_path if vector_db_path is None else vector_db_path
        return regress_and_persist(
            repository=self.repository,
            packs_dir=self.packs_dir,
            corpus_dir=self.corpus_dir,
            seeds_dir=seeds_dir,
            rounds=rounds,
            max_seeds=max_seeds,
            metric_set=metric_set,
            min_community_coverage=min_community_coverage,
            min_conflict_frame_runs=min_conflict_frame_runs,
            min_moderation_hook_runs=min_moderation_hook_runs,
            min_validation_warning_runs=min_validation_warning_runs,
            orchestrator_backend=orchestrator_backend,
            vector_backend=resolved_vector_backend,
            vector_db_path=resolved_vector_db_path,
        )

    def _build_kb_index(self) -> dict:
        packs = load_packs(self.packs_dir, enforce_phase1_minimums=True)
        return build_index(
            packs,
            corpus_dir=self.corpus_dir,
            vector_backend=self.vector_backend,
            vector_db_path=self.vector_db_path,
        )

    def search_knowledge(
        self, *, query: str, filters: dict | None = None, top_k: int = 5
    ) -> dict:
        index = self._build_kb_index()
        items = search(index, query=query, filters=filters or {}, top_k=top_k)
        return {"count": len(items), "items": items}

    def get_pack_item(self, pack: str, item_id: str) -> dict:
        index = self._build_kb_index()
        item = kb_get_pack_item(index, pack, item_id)
        if item is None:
            raise FileNotFoundError(f"Pack item not found: {pack}/{item_id}")
        return item

    def retrieve_context_bundle(
        self,
        *,
        task: str,
        seed: str,
        board_id: str,
        zone_id: str,
        persona_ids: list[str] | None = None,
        top_k: int = 3,
    ) -> dict:
        index = self._build_kb_index()
        return retrieve_context(
            index,
            task=task,
            seed=seed,
            board_id=board_id,
            zone_id=zone_id,
            persona_ids=persona_ids or [],
            top_k=top_k,
        )
