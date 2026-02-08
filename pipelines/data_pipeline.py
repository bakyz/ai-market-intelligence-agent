import json
import re
from pathlib import Path
from typing import Iterable, List

from app.config.settings import get_settings
from app.llm.client import LLMWrapper
from app.llm.model_router import ModelRouter
from app.llm.prompts.template import format_analysis_prompt

settings = get_settings()

DEFAULT_SECTOR = "startups & emerging tech"

DEFAULT_KEY_METRICS = (
    "pain points, unmet needs, traction signals, "
    "pricing hints, and competitive alternatives"
)

def load_json_records(path: Path) -> List[dict]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def preprocess_text(title: str | None, body: str | None) -> str:
    combined = " ".join([segment for segment in [title, body] if segment]).strip()

    combined = combined.lower()
    combined = re.sub(r"http\S+|www\.\S+", "", combined)
    combined = re.sub(r"[^\w\s\-\.,!?]", "", combined)
    combined = re.sub(r"\s+", " ", combined)

    return combined.strip()

def iter_batches(items: List[str], batch_size: int) -> Iterable[List[str]]:
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    embeddings: List[List[float]] = []

    for batch in iter_batches(texts, batch_size=50):
        response = client.embeddings.create(
            model=settings.model.EMBEDDING_MODEL,
            input=batch
        )

        ordered = sorted(response.data, key=lambda item: item.index)
        embeddings.extend([item.embedding for item in ordered])

    return embeddings

def generate_market_analysis(llm: LLMWrapper, text: str, source: str) -> str:
    prompt = format_analysis_prompt(
        sector=DEFAULT_SECTOR,
        data=f"Source: {source}\n\nContent: {text}",
        key_metrics=DEFAULT_KEY_METRICS,
    )

    return llm.query(
        prompt,
        system_prompt=(
            "You are a senior market research analyst. "
            "Extract startup pain points, unmet needs, and market signals."
        ),
    )

def build_processed_records(raw_records: List[dict]) -> List[dict]:

    cleaned_texts = [
        preprocess_text(record.get("title"), record.get("body"))
        for record in raw_records
    ]

    embeddings = generate_embeddings(cleaned_texts)

    analysis_model = ModelRouter.get_model_for_task("synthesis")
    llm = LLMWrapper(model=analysis_model)

    processed_records: List[dict] = []

    for record, cleaned_text, embedding in zip(
        raw_records, cleaned_texts, embeddings
    ):
        processed_records.append(
            {
                "title": record.get("title"),
                "body": record.get("body"),
                "score": record.get("score"),
                "comments": record.get("comments"),
                "created_at": record.get("created_at"),
                "source": record.get("source"),
                "cleaned_text": cleaned_text,
                "embedding": embedding,
                "market_analysis": generate_market_analysis(
                    llm,
                    cleaned_text,
                    record.get("source", "unknown"),
                ),
            }
        )

    return processed_records

def run_pipeline() -> Path:
    raw_path = Path(settings.paths.RAW_DATA)
    processed_path = Path(settings.paths.PROCESSED_DATA)
    processed_path.mkdir(parents=True, exist_ok=True)

    reddit_records = load_json_records(raw_path / "reddit.json")
    hn_records = load_json_records(raw_path / "hn.json")

    combined_records = reddit_records + hn_records

    processed_records = build_processed_records(combined_records)

    output_file = processed_path / "market_analysis.json"

    with output_file.open("w", encoding="utf-8") as handle:
        json.dump(processed_records, handle, ensure_ascii=False, indent=2)

    print(f"Processed {len(processed_records)} records -> {output_file}")

    return output_file


if __name__ == "__main__":
    run_pipeline()
