from pathlib import Path


def test_readme_contains_quickstart():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "pytest" in text
    assert "simulate" in text
