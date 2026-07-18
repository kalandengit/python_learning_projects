"""Build the fine-tuning dataset (Mistral JSONL chat format).

Sources:
1. logs/chat_log.jsonl — only exchanges you rated 👍 ("good") in the UI.
2. finetune_data/manual/*.jsonl — hand-written examples (see manual/example.jsonl).

Output:
  finetune_data/train.jsonl  (90%)
  finetune_data/eval.jsonl   (10%, held out for evaluation)

Run:  python -m app.finetune.dataset
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from app.config import settings, setup_logging
from app.rag.persona import CONSORTIUM_PROMPT

logger = setup_logging()

MIN_EXAMPLES = 20  # below this, fine-tuning is not worth running


def _record(question: str, answer: str) -> dict:
    """One Mistral fine-tuning example in chat format."""
    return {
        "messages": [
            {"role": "system", "content": CONSORTIUM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


def _from_chat_log() -> list[dict]:
    path = settings.logs_dir / "chat_log.jsonl"
    if not path.exists():
        return []
    examples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("rating") == "good" and rec.get("question") and rec.get("answer"):
            examples.append(_record(rec["question"], rec["answer"]))
    return examples


def _validate_manual(rec: dict, source: str) -> bool:
    msgs = rec.get("messages")
    if not isinstance(msgs, list) or len(msgs) < 2:
        logger.warning("Skipping invalid record in %s (need a 'messages' list)", source)
        return False
    roles = [m.get("role") for m in msgs]
    if roles[-1] != "assistant" or "user" not in roles:
        logger.warning("Skipping record in %s (must end with an assistant turn)", source)
        return False
    return all(isinstance(m.get("content"), str) and m["content"].strip() for m in msgs)


def _from_manual() -> list[dict]:
    manual_dir = settings.finetune_dir / "manual"
    examples = []
    for path in sorted(manual_dir.glob("*.jsonl")):
        if path.name == "example.jsonl":  # documentation sample, not training data
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Bad JSON line in %s", path.name)
                continue
            if _validate_manual(rec, path.name):
                examples.append(rec)
    return examples


def build(seed: int = 42) -> tuple[Path, Path, int, int]:
    """Assemble, shuffle, split, and write train/eval JSONL. Returns paths and counts."""
    examples = _from_chat_log() + _from_manual()
    if len(examples) < MIN_EXAMPLES:
        raise SystemExit(
            f"Only {len(examples)} usable examples (need ≥{MIN_EXAMPLES}).\n"
            "Rate more answers 👍 in the chat UI, or add files to finetune_data/manual/ "
            "(format: finetune_data/manual/example.jsonl). See docs/en/05-finetuning.md."
        )
    random.Random(seed).shuffle(examples)
    n_eval = max(2, len(examples) // 10)
    eval_set, train_set = examples[:n_eval], examples[n_eval:]

    settings.finetune_dir.mkdir(parents=True, exist_ok=True)
    train_path = settings.finetune_dir / "train.jsonl"
    eval_path = settings.finetune_dir / "eval.jsonl"
    for path, dataset in ((train_path, train_set), (eval_path, eval_set)):
        with path.open("w", encoding="utf-8") as f:
            for rec in dataset:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return train_path, eval_path, len(train_set), len(eval_set)


if __name__ == "__main__":
    train_path, eval_path, n_train, n_eval = build()
    print(f"✓ {train_path}  ({n_train} examples)")
    print(f"✓ {eval_path}   ({n_eval} examples)")
    print("Next: python -m app.finetune.train")
