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
    assert len(client.calls) == 2
    assert client.calls[0]["task"] == "comment_stage1"
    assert client.calls[1]["task"] == "comment_generation"
    assert "board=B07 zone=D round=2 persona=P-777" in client.calls[0]["prompt"]
    assert "claim=" in client.calls[1]["prompt"]
    assert "evidence=" in client.calls[1]["prompt"]
    assert "intent=" in client.calls[1]["prompt"]


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
    assert len(client.calls) == 2
    assert client.calls[0]["task"] == "comment_stage1"
    assert client.calls[1]["task"] == "comment_generation"


def test_generator_includes_voice_hint_when_provided():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate(self, prompt: str, *, task: str) -> str:
            self.calls.append({"prompt": prompt, "task": task})
            return prompt

    seed = SeedInput(seed_id="SEED-004", title="사건4", summary="요약4", board_id="B04", zone_id="B")
    client = FakeClient()

    output = generate_comment(
        seed,
        "P-202",
        round_idx=1,
        llm_client=client,
        voice_constraints={
            "sentence_length": "short",
            "endings": ["임", "각"],
            "taboo_words": ["injury_dox", "doping_claim_no_proof"],
        },
    )

    assert "voice=style:short;endings:임/각;taboo_count:2" in output
    assert len(client.calls) == 2
    assert client.calls[0]["task"] == "comment_stage1"
    assert client.calls[1]["task"] == "comment_generation"


def test_generator_uses_stage1_structured_output_when_json_provided():
    class FakeClient:
        def __init__(self):
            self.calls = []

        def generate(self, prompt: str, *, task: str) -> str:
            self.calls.append({"prompt": prompt, "task": task})
            if task == "comment_stage1":
                return '{"claim":"운영 공지 누락","evidence":"로그 캡처 2건","intent":"mediate"}'
            return prompt

    seed = SeedInput(
        seed_id="SEED-005",
        title="사건5",
        summary="요약5",
        board_id="B09",
        zone_id="C",
    )
    client = FakeClient()

    output = generate_comment(
        seed,
        "P-303",
        round_idx=2,
        llm_client=client,
        memory_hint="R1: 캡처 확인 요청",
        voice_constraints={"sentence_length": "short", "endings": ["임"], "taboo_words": []},
    )

    assert len(client.calls) == 2
    assert client.calls[0]["task"] == "comment_stage1"
    assert client.calls[1]["task"] == "comment_generation"
    assert "claim=운영 공지 누락" in client.calls[1]["prompt"]
    assert "evidence=로그 캡처 2건" in client.calls[1]["prompt"]
    assert "intent=mediate" in client.calls[1]["prompt"]
    assert "dial=U30-E25-M15-S15-H15" in client.calls[1]["prompt"]
    assert "voice=style:short;endings:임;taboo_count:0" in output
