from project_dream.models import SeedInput
from project_dream.persona_service import select_participants
from project_dream.gen_engine import generate_comment


def test_generator_is_deterministic_for_same_seed():
    seed = SeedInput(seed_id="SEED-001", title="사건", summary="요약", board_id="B01", zone_id="A")
    participants = select_participants(seed, round_idx=1)
    c1 = generate_comment(seed, participants[0], round_idx=1)
    c2 = generate_comment(seed, participants[0], round_idx=1)
    assert c1 == c2


def test_generator_accepts_custom_llm_client():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate(self, prompt: str, *, task: str) -> str:
            self.calls.append({"prompt": prompt, "task": task})
            return f"FAKE::{prompt}"

    seed = SeedInput(seed_id="SEED-002", title="사건2", summary="요약2", board_id="B07", zone_id="D")
    client = FakeClient()

    output = generate_comment(seed, "P-777", round_idx=2, llm_client=client)

    assert output.startswith("FAKE::")
    assert len(client.calls) == 1
    assert client.calls[0]["task"] == "comment_generation"
    assert "[B07/D] R2 P-777" in client.calls[0]["prompt"]


def test_generator_includes_memory_hint_when_provided():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate(self, prompt: str, *, task: str) -> str:
            self.calls.append({"prompt": prompt, "task": task})
            return prompt

    seed = SeedInput(seed_id="SEED-003", title="사건3", summary="요약3", board_id="B03", zone_id="B")
    client = FakeClient()

    output = generate_comment(
        seed,
        "P-101",
        round_idx=3,
        llm_client=client,
        memory_hint="R2: 이전에는 근거 링크를 먼저 요구했다",
    )

    assert "memory=R2: 이전에는 근거 링크를 먼저 요구했다" in output
    assert len(client.calls) == 1
