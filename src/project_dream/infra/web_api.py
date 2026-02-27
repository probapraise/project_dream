from pathlib import Path

from project_dream.app_service import evaluate_and_persist, simulate_and_persist
from project_dream.infra.store import FileRunRepository, RunRepository
from project_dream.models import SeedInput


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
