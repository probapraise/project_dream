def build_report(seed, sim_result: dict) -> dict:
    return {
        "seed_id": seed.seed_id,
        "summary": f"{seed.title} / 라운드 {len(sim_result['rounds'])}",
        "highlights": sim_result["rounds"][:10],
        "risks": [
            row
            for row in sim_result["gate_logs"]
            if any(not gate["passed"] for gate in row["gates"])
        ],
    }
