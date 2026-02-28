from project_dream.models import SeedInput
import project_dream.sim_orchestrator as sim_orchestrator


def _always_pass_gates(text: str, corpus: list[str]) -> dict:
    return {
        "final_text": text,
        "gates": [
            {"gate_name": "safety", "passed": True},
            {"gate_name": "similarity", "passed": True},
            {"gate_name": "lore", "passed": True},
        ],
    }


def test_simulation_reuses_persona_memory_hint(monkeypatch):
    captured_calls: list[dict] = []

    def fake_generate_comment(
        seed,
        persona_id: str,
        round_idx: int,
        llm_client=None,
        template_set: str = "v1",
        memory_hint: str | None = None,
        voice_constraints: dict | None = None,
        template_context: dict | None = None,
        flow_context: dict | None = None,
    ) -> str:
        captured_calls.append(
            {
                "round_idx": round_idx,
                "persona_id": persona_id,
                "memory_hint": memory_hint or "",
            }
        )
        return f"{persona_id}-R{round_idx}-comment"

    monkeypatch.setattr(sim_orchestrator, "generate_comment", fake_generate_comment)
    monkeypatch.setattr(
        sim_orchestrator,
        "select_participants",
        lambda seed, round_idx, packs=None: ["P07", "P08", "P09"],
    )
    monkeypatch.setattr(sim_orchestrator, "run_gates", _always_pass_gates)

    seed = SeedInput(
        seed_id="SEED-MEM-001",
        title="메모리 사건",
        summary="라운드 간 메모가 유지되어야 한다",
        board_id="B07",
        zone_id="D",
    )

    result = sim_orchestrator.run_simulation(seed=seed, rounds=2, corpus=["샘플"], packs=None)

    round1_p07 = [row for row in captured_calls if row["round_idx"] == 1 and row["persona_id"] == "P07"][0]
    round2_p07 = [row for row in captured_calls if row["round_idx"] == 2 and row["persona_id"] == "P07"][0]

    assert round1_p07["memory_hint"] == ""
    assert round2_p07["memory_hint"] != ""
    assert "R1" in round2_p07["memory_hint"]
    assert result["persona_memory"]["P07"]


def test_round_logs_include_memory_fields():
    seed = SeedInput(
        seed_id="SEED-MEM-002",
        title="메모리 로그 사건",
        summary="라운드 로그에 메모리 상태를 기록한다",
        board_id="B01",
        zone_id="A",
    )

    result = sim_orchestrator.run_simulation(seed=seed, rounds=2, corpus=["샘플"], packs=None)

    assert result["rounds"]
    first = result["rounds"][0]
    assert "memory_before" in first
    assert "memory_after" in first
    assert isinstance(first["memory_before"], str)
    assert isinstance(first["memory_after"], str)


def test_memory_hint_excludes_system_rewrite_artifacts(monkeypatch):
    captured_calls: list[dict] = []

    def fake_generate_comment(
        seed,
        persona_id: str,
        round_idx: int,
        llm_client=None,
        template_set: str = "v1",
        memory_hint: str | None = None,
        voice_constraints: dict | None = None,
        template_context: dict | None = None,
        flow_context: dict | None = None,
    ) -> str:
        captured_calls.append(
            {
                "round_idx": round_idx,
                "persona_id": persona_id,
                "memory_hint": memory_hint or "",
            }
        )
        return f"{persona_id}-R{round_idx}-comment"

    def fake_lore_fail_gates(text: str, corpus: list[str]) -> dict:
        return {
            "final_text": f"{text} / 근거(정본/증거/로그) 기준 추가 필요",
            "gates": [
                {"gate_name": "safety", "passed": True},
                {"gate_name": "similarity", "passed": True},
                {"gate_name": "lore", "passed": False},
            ],
        }

    monkeypatch.setattr(sim_orchestrator, "generate_comment", fake_generate_comment)
    monkeypatch.setattr(
        sim_orchestrator,
        "select_participants",
        lambda seed, round_idx, packs=None: ["P07", "P08", "P09"],
    )
    monkeypatch.setattr(sim_orchestrator, "run_gates", fake_lore_fail_gates)

    seed = SeedInput(
        seed_id="SEED-MEM-003",
        title="메모리 정제 사건",
        summary="시스템 재작성 문구는 메모리에 누적되면 안 된다",
        board_id="B07",
        zone_id="D",
    )
    result = sim_orchestrator.run_simulation(seed=seed, rounds=2, corpus=["샘플"], max_retries=0, packs=None)

    round2_p07 = [row for row in captured_calls if row["round_idx"] == 2 and row["persona_id"] == "P07"][0]
    assert "근거(정본/증거/로그)" not in round2_p07["memory_hint"]
    assert "| memory=" not in round2_p07["memory_hint"]
    assert all("근거(정본/증거/로그)" not in entry for entry in result["persona_memory"]["P07"])
