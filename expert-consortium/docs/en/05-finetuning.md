# 5 — Fine-tuning your own model (English)

Fine-tuning creates **your personal Mistral model** — trained on your best Q&A exchanges so
it adopts your domains, your style, your terminology. It runs entirely on Mistral's servers:
**no GPU needed on your side.**

## When is it worth doing?

✅ Do it when:
- You have used the assistant for a while and rated **at least 50–100 answers 👍**
  (20 is the technical minimum; 100+ gives real results).
- You want a cheaper model (`ministral-8b`) to answer as well as an expensive one on
  *your* topics.
- You want stylistic consistency (e.g., always cite articles the same way).

❌ Don't bother when:
- You just added new documents — that's RAG's job, no training needed.
- You have few rated examples — the model will barely change.

**Important:** fine-tuning does NOT replace the document database. Your fine-tuned model
still uses RAG; it just becomes better at *using* it in your style.

## Step 1 — Collect training data (ongoing)

Two sources, mixed automatically:

1. **👍 ratings in the chat** — every answer you rate "good" becomes a training example.
2. **Manual examples** — write perfect Q&A pairs in `finetune_data/manual/my-examples.jsonl`,
   one JSON per line, following the format in `finetune_data/manual/example.jsonl`.
   These are gold: 20 hand-written perfect answers beat 200 mediocre ones.

## Step 2 — Build the dataset

```bash
python -m app.finetune.dataset
```

Creates `finetune_data/train.jsonl` (90%) and `finetune_data/eval.jsonl` (10% held out to
measure honestly). Refuses to run with fewer than 20 examples.

## Step 3 — Launch the training

```bash
python -m app.finetune.train
```

Uploads the dataset and starts the job on Mistral's servers (default base:
`ministral-8b-latest` — cheap and fast; use `--model open-mistral-7b` or others to compare).
The command follows progress until done (typically minutes to ~1 hour; cost ~$1–10). At the
end it prints your model id, like `ft:ministral-8b:xxxx:yyyy`.

## Step 4 — Compare honestly before adopting

```bash
python -m app.finetune.evaluate --finetuned ft:ministral-8b:xxxx:yyyy
```

Both models answer the held-out eval questions with the same document context; an impartial
judge model picks the better answer each time. Read the verdict and the full side-by-side
report in `finetune_data/evaluation_report.md`.

## Step 5 — Adopt it (if it won)

In `.env`:

```
CHAT_MODEL=ft:ministral-8b:xxxx:yyyy
```

Restart the app. To go back, restore `CHAT_MODEL=mistral-large-latest`.

## About N'Ko (Phase 3 of the PRD)

Fine-tuning on your rated exchanges will NOT teach the model fluent N'Ko — that requires a
dedicated parallel corpus (N'Ko ↔ French sentence pairs) in the thousands. If you build such
a corpus (your ingested N'Ko documents are a starting point), the same
`finetune_data/manual/` mechanism accepts it: each line a translation or explanation pair.
Treat results as experimental and have them checked by a literate N'Ko reader.

**Next:** [6 — Deployment](06-deploy-vps.md)
