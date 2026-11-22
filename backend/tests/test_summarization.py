from types import SimpleNamespace

from app.services import summarization


def test_structured_summary_marks_missing_information(monkeypatch):
    monkeypatch.setattr(summarization, "summarize_long_text", lambda _text, detail: f"{detail} overview")
    paper = SimpleNamespace(title="A Paper", abstract="This study aims to test an approach.")
    text = """ABSTRACT
This study aims to test an approach and address a difficult problem.
INTRODUCTION
The challenge remains difficult for existing methods.
METHODS
We propose a transformer model trained with an attention mechanism.
RESULTS
Results show improved accuracy on the dataset.
LIMITATIONS
The study is limited by a small sample.
FUTURE WORK
Future work will examine larger studies.
"""

    summary = summarization.create_structured_summary(paper, text, detail="short")

    assert summary["research_title"] == "A Paper"
    assert "aims to test" in summary["research_objective"]
    assert "transformer" in summary["transformer_architecture_or_algorithm"]
    assert summary["dataset_used"] != "Not stated in the extracted paper text."
    assert "improved accuracy" in summary["advantages"]
    assert summary["overview"] == "short overview"
