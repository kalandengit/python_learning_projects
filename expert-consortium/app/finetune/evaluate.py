"""Compare the base model vs your fine-tuned model on the held-out eval set.

For each eval question, both models answer (with the same RAG context) and the chat model
acts as an impartial judge. Results land in finetune_data/evaluation_report.md.

Run:  python -m app.finetune.evaluate --finetuned ft:your-model-id
"""

from __future__ import annotations

import argparse
import json

from app.config import settings, setup_logging
from app.mistral_client import get_client, with_retry
from app.rag.persona import build_messages
from app.rag.retriever import retrieve

logger = setup_logging()

JUDGE_PROMPT = """\
You are an impartial judge. Two AI answers (A and B) to the same question follow, plus a
reference answer the user previously rated as good. Score which answer is closer in
accuracy, citation quality, and helpfulness to the reference.
Reply with EXACTLY one word: A, B, or TIE.

Question: {question}

Reference answer:
{reference}

Answer A:
{a}

Answer B:
{b}
"""


def _answer(model: str, question: str) -> str:
    chunks = retrieve(question)
    messages = build_messages(question, [(c.source_file, c.text) for c in chunks])
    resp = with_retry(
        get_client().chat.complete, model=model, messages=messages, temperature=0.3
    )
    return resp.choices[0].message.content or ""


def _judge(question: str, reference: str, a: str, b: str) -> str:
    resp = with_retry(
        get_client().chat.complete,
        model="mistral-large-latest",
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            question=question, reference=reference, a=a, b=b)}],
        temperature=0.0,
    )
    verdict = (resp.choices[0].message.content or "").strip().upper()
    return verdict if verdict in ("A", "B", "TIE") else "TIE"


def evaluate(finetuned: str, base: str, limit: int) -> None:
    eval_path = settings.finetune_dir / "eval.jsonl"
    if not eval_path.exists():
        raise SystemExit("No eval.jsonl — run: python -m app.finetune.dataset")

    examples = []
    for line in eval_path.read_text(encoding="utf-8").splitlines()[:limit]:
        rec = json.loads(line)
        user_msgs = [m for m in rec["messages"] if m["role"] == "user"]
        examples.append((user_msgs[-1]["content"], rec["messages"][-1]["content"]))

    wins = {"base": 0, "finetuned": 0, "tie": 0}
    rows = []
    for i, (question, reference) in enumerate(examples, 1):
        print(f"[{i}/{len(examples)}] {question[:70]}...")
        base_answer = _answer(base, question)
        ft_answer = _answer(finetuned, question)
        # A = base, B = fine-tuned
        verdict = _judge(question, reference, base_answer, ft_answer)
        key = {"A": "base", "B": "finetuned", "TIE": "tie"}[verdict]
        wins[key] += 1
        rows.append((question, base_answer, ft_answer, key))

    report = settings.finetune_dir / "evaluation_report.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Fine-tuning evaluation report\n\n")
        f.write(f"Base model: `{base}` — Fine-tuned: `{finetuned}`\n\n")
        f.write(f"**Result: fine-tuned wins {wins['finetuned']}, "
                f"base wins {wins['base']}, ties {wins['tie']}**\n\n")
        for question, base_answer, ft_answer, winner in rows:
            f.write(f"---\n\n### {question}\n\n*Winner: {winner}*\n\n"
                    f"**Base:**\n\n{base_answer}\n\n**Fine-tuned:**\n\n{ft_answer}\n\n")
    print(f"\nFine-tuned wins {wins['finetuned']}, base wins {wins['base']}, "
          f"ties {wins['tie']} — details in {report}")
    if wins["finetuned"] > wins["base"]:
        print(f"👍 Your fine-tuned model is better — set CHAT_MODEL={finetuned} in .env")
    else:
        print("🤔 The base model still wins — collect more 👍-rated examples and retrain.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--finetuned", required=True, help="fine-tuned model id (ft:...)")
    parser.add_argument("--base", default=settings.chat_model, help="base model to compare")
    parser.add_argument("--limit", type=int, default=20, help="max eval questions")
    args = parser.parse_args()
    evaluate(args.finetuned, args.base, args.limit)


if __name__ == "__main__":
    main()
