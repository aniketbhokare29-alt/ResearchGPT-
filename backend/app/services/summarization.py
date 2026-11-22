import re
import threading
from datetime import datetime, timezone

from app.core.config import settings

_pipeline_lock = threading.Lock()
_summarizer = None
_sections = (
    "abstract", "introduction", "background", "related work", "method", "methods", "methodology",
    "approach", "materials and methods", "proposed method", "experiments", "experimental setup",
    "results", "results and discussion", "discussion", "conclusion", "limitations", "limitations and future work",
    "future work", "future scope", "references", "bibliography", "acknowledgements", "acknowledgments",
)


def _get_summarizer():
    global _summarizer
    if _summarizer is None:
        with _pipeline_lock:
            if _summarizer is None:
                import torch
                from transformers import pipeline

                device = settings.model_device
                if device == "auto":
                    device = 0 if torch.cuda.is_available() else -1
                elif device == "cpu":
                    device = -1
                elif device.startswith("cuda"):
                    device = int(device.split(":", 1)[1]) if ":" in device else 0
                _summarizer = pipeline("summarization", model=settings.summary_model_name, device=device)
    return _summarizer


def _token_chunks(text: str, tokenizer, max_tokens: int) -> list[str]:
    token_ids = tokenizer.encode(text, add_special_tokens=False)
    if not token_ids:
        return []
    stride = max(64, max_tokens - 96)
    parts = []
    for start in range(0, len(token_ids), stride):
        piece = tokenizer.decode(token_ids[start : start + max_tokens], skip_special_tokens=True)
        if piece.strip():
            parts.append(piece)
        if start + max_tokens >= len(token_ids):
            break
    return parts


def summarize_long_text(text: str, detail: str = "short") -> str:
    summarizer = _get_summarizer()
    tokenizer = summarizer.tokenizer
    model_limit = getattr(summarizer.model.config, "max_position_embeddings", settings.summary_max_input_tokens)
    input_limit = min(settings.summary_max_input_tokens, int(model_limit) - 16)
    chunks = _token_chunks(text, tokenizer, input_limit)
    if not chunks:
        return "No extractable text was available for summarization."

    output_limit = min(settings.summary_max_output_tokens, 170 if detail == "detailed" else 90)
    summaries = []
    for chunk in chunks:
        generated = summarizer(
            chunk,
            max_new_tokens=output_limit,
            min_new_tokens=min(20, output_limit // 3),
            truncation=True,
            do_sample=False,
        )
        summaries.append(generated[0]["summary_text"].strip())

    # Map-reduce summaries keep the complete paper represented without feeding the
    # entire document into a model that cannot accept it.
    for _level in range(3):
        if len(summaries) <= 1:
            break
        reduced_input = "\n".join(summaries)
        reduced_chunks = _token_chunks(reduced_input, tokenizer, input_limit)
        reduced = []
        for chunk in reduced_chunks:
            generated = summarizer(
                chunk,
                max_new_tokens=output_limit,
                min_new_tokens=min(20, output_limit // 3),
                truncation=True,
                do_sample=False,
            )
            reduced.append(generated[0]["summary_text"].strip())
        if len(reduced) >= len(summaries):
            break
        summaries = reduced
    return "\n\n".join(summaries)


def _section_map(text: str) -> dict[str, str]:
    names = "|".join(re.escape(name) for name in sorted(_sections, key=len, reverse=True))
    heading = re.compile(
        rf"(?im)^\s*(?:(?:\d+(?:\.\d+)*|[IVX]+)[.)]?\s*)?({names})\s*[:.]?\s*$"
    )
    matches = list(heading.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = re.sub(r"\s+", " ", match.group(1).lower())
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[match.end() : end].strip()
        if content:
            result[name] = content
    return result


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text) if len(part.strip()) > 25]


def _selected_sentences(text: str, patterns: tuple[str, ...], cap: int = 5) -> str | None:
    sentences = _sentences(text)
    matches = [sentence for sentence in sentences if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)]
    selected = matches[:cap]
    return " ".join(selected)[:5000] if selected else None


def create_structured_summary(paper, page_text: str, detail: str = "short") -> dict:
    if detail not in {"short", "detailed"}:
        raise ValueError("Summary detail must be short or detailed.")
    sections = _section_map(page_text)
    abstract = paper.abstract or sections.get("abstract", "")
    introduction = sections.get("introduction", sections.get("background", ""))
    methodology = next(
        (sections[name] for name in ("methodology", "methods", "method", "approach", "materials and methods", "proposed method") if sections.get(name)),
        "",
    )
    results = sections.get("results and discussion", sections.get("results", sections.get("discussion", "")))
    limitations = sections.get("limitations", sections.get("limitations and future work", ""))
    future = sections.get("future work", sections.get("future scope", ""))
    base = abstract or introduction or page_text
    objective = _selected_sentences(
        base + "\n" + introduction,
        (r"\b(objective|aim|purpose|we propose|this paper proposes|we present|this paper presents)\b",),
        cap=6 if detail == "detailed" else 3,
    )
    if not objective:
        objective = " ".join(_sentences(base)[: (4 if detail == "detailed" else 2)]) or None
    problem = _selected_sentences(
        abstract + "\n" + introduction,
        (r"\b(problem|challenge|difficulty|gap|limited|lack of|remains unresolved)\b",),
        cap=6 if detail == "detailed" else 3,
    )
    architecture = _selected_sentences(
        page_text,
        (r"\b(transformer|bert|t5|bart|vit|vision transformer|attention mechanism|algorithm)\b",),
        cap=8 if detail == "detailed" else 4,
    )
    datasets = _selected_sentences(
        page_text,
        (r"\b(dataset|benchmark|corpus|train(?:ing)? set|test set)\b",),
        cap=8 if detail == "detailed" else 4,
    )
    result_facts = _selected_sentences(
        results or page_text,
        (r"\b(result|achiev|accuracy|precision|recall|f1|bleu|rouge|compared to|outperform|improv)\w*\b",),
        cap=8 if detail == "detailed" else 4,
    )
    advantages = _selected_sentences(
        results or abstract,
        (r"\b(improv|outperform|state.of.the.art|benefit|efficient|robust|reduc)\w*\b",),
        cap=6 if detail == "detailed" else 3,
    )
    limitation_facts = limitations or _selected_sentences(
        page_text,
        (r"\b(limitation|shortcoming|threat to validity|does not address|future work)\b",),
        cap=6 if detail == "detailed" else 3,
    )
    future_facts = future or _selected_sentences(
        page_text,
        (r"\b(future work|future research|further research|we plan to|will investigate)\b",),
        cap=6 if detail == "detailed" else 3,
    )

    max_chars = 5000 if detail == "detailed" else 2400
    missing = "Not stated in the extracted paper text."
    return {
        "detail": detail,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "research_title": paper.title or missing,
        "research_objective": (objective or missing)[:max_chars],
        "problem_statement": (problem or missing)[:max_chars],
        "proposed_methodology": (methodology or _selected_sentences(abstract, (r"\b(method|approach|model|propose)\b",), 4) or missing)[:max_chars],
        "transformer_architecture_or_algorithm": (architecture or missing)[:max_chars],
        "dataset_used": (datasets or missing)[:max_chars],
        "experimental_results": (result_facts or missing)[:max_chars],
        "advantages": (advantages or missing)[:max_chars],
        "limitations": (limitation_facts or missing)[:max_chars],
        "future_scope": (future_facts or missing)[:max_chars],
        "overview": summarize_long_text(page_text, detail=detail),
        "note": "Structured fields are extracted from the paper text. The overview is generated by the configured pretrained summarization model.",
    }
