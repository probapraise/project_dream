from pathlib import Path

from project_dream.app_service import evaluate_and_persist, regress_and_persist, simulate_and_persist
from project_dream.kb_index import build_index, get_pack_item as kb_get_pack_item, retrieve_context, search
from project_dream.infra.store import FileRunRepository, RunRepository
from project_dream.models import SeedInput
from project_dream.pack_service import load_packs


class ProjectDreamAPI:
    def __init__(self, repository: RunRepository, packs_dir: Path):
        self.repository = repository
        self.packs_dir = packs_dir

    @classmethod
    def for_local_filesystem(
        cls,
        *,
        runs_dir: Path = Path("runs"),
        packs_dir: Path = Path("packs"),
    ) -> "ProjectDreamAPI":
        return cls(repository=FileRunRepository(runs_dir), packs_dir=packs_dir)

    def health(self) -> dict:
        return {"status": "ok", "service": "project-dream"}

    def simulate(self, seed_payload: dict, rounds: int = 3) -> dict:
        seed = SeedInput.model_validate(seed_payload)
        run_dir = simulate_and_persist(
            seed,
            rounds=rounds,
            packs_dir=self.packs_dir,
            repository=self.repository,
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

    def list_regression_summaries(self, limit: int | None = None) -> dict:
        return self.repository.list_regression_summaries(limit=limit)

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
    ) -> dict:
        return regress_and_persist(
            repository=self.repository,
            packs_dir=self.packs_dir,
            seeds_dir=seeds_dir,
            rounds=rounds,
            max_seeds=max_seeds,
            metric_set=metric_set,
            min_community_coverage=min_community_coverage,
            min_conflict_frame_runs=min_conflict_frame_runs,
            min_moderation_hook_runs=min_moderation_hook_runs,
            min_validation_warning_runs=min_validation_warning_runs,
        )

    def _build_kb_index(self) -> dict:
        packs = load_packs(self.packs_dir, enforce_phase1_minimums=True)
        return build_index(packs)

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
