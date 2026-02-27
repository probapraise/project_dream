from project_dream.gen_engine import generate_comment
from project_dream.gate_pipeline import run_gates
from project_dream.persona_service import select_participants


def run_simulation(seed, rounds: int, corpus: list[str], max_retries: int = 2) -> dict:
    round_logs: list[dict] = []
    gate_logs: list[dict] = []

    for round_idx in range(1, rounds + 1):
        participants = select_participants(seed, round_idx=round_idx)[:3]

        for persona_id in participants:
            text = generate_comment(seed, persona_id, round_idx=round_idx)
            last = None

            for _ in range(max_retries + 1):
                last = run_gates(text, corpus=corpus)
                if all(g["passed"] for g in last["gates"]):
                    break
                text = last["final_text"]

            assert last is not None
            round_logs.append({"round": round_idx, "persona_id": persona_id, "text": last["final_text"]})
            gate_logs.append({"round": round_idx, "persona_id": persona_id, "gates": last["gates"]})

    return {"rounds": round_logs, "gate_logs": gate_logs}
