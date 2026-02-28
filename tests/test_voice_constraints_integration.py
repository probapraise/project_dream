from project_dream.models import SeedInput
import project_dream.sim_orchestrator as sim_orchestrator


def test_orchestrator_passes_rendered_voice_to_generator(monkeypatch):
    calls: list[dict] = []

    def fake_generate_comment(
        seed,
        persona_id: str,
        round_idx: int,
        llm_client=None,
        template_set: str = "v1",
        memory_hint: str | None = None,
        voice_constraints: dict | None = None,
    ) -> str:
        calls.append(
            {
                "persona_id": persona_id,
                "voice_constraints": voice_constraints or {},
            }
        )
        return f"{persona_id}-R{round_idx}"

    monkeypatch.setattr(sim_orchestrator, "generate_comment", fake_generate_comment)
    monkeypatch.setattr(
        sim_orchestrator,
        "select_participants",
        lambda seed, round_idx, packs=None: ["P07", "P08", "P09"],
    )
    monkeypatch.setattr(
        sim_orchestrator,
        "render_voice",
        lambda persona_id, zone_id, packs=None: {
            "persona_id": persona_id,
            "zone_id": zone_id,
            "sentence_length": "short",
            "endings": ["임", "각"],
            "frequent_words": ["과열"],
            "taboo_words": ["fake_review"],
        },
    )
    monkeypatch.setattr(
        sim_orchestrator,
        "run_gates",
        lambda text, corpus: {
            "final_text": text,
            "gates": [
                {"gate_name": "safety", "passed": True},
                {"gate_name": "similarity", "passed": True},
                {"gate_name": "lore", "passed": True},
            ],
        },
    )

    seed = SeedInput(
        seed_id="SEED-VOICE-001",
        title="보이스 사건",
        summary="말투 제약 전달 테스트",
        board_id="B07",
        zone_id="D",
    )
    result = sim_orchestrator.run_simulation(seed=seed, rounds=1, corpus=["샘플"], packs=None)

    assert calls
    assert calls[0]["voice_constraints"]["sentence_length"] == "short"
    assert calls[0]["voice_constraints"]["endings"] == ["임", "각"]
    assert result["rounds"][0]["voice_style"] == "short"
