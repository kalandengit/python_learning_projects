"""Launch and monitor a Mistral fine-tuning job (runs on Mistral's servers — no GPU here).

Run:
    python -m app.finetune.train                 # launch with defaults
    python -m app.finetune.train --model open-mistral-7b
    python -m app.finetune.train --status JOB_ID # check an existing job
"""

from __future__ import annotations

import argparse
import time

from app.config import settings, setup_logging
from app.mistral_client import get_client, with_retry

logger = setup_logging()

DEFAULT_BASE_MODEL = "ministral-8b-latest"


def upload_file(path) -> str:
    client = get_client()
    resp = with_retry(
        client.files.upload,
        file={"file_name": path.name, "content": path.read_bytes()},
        purpose="fine-tune",
    )
    print(f"✓ Uploaded {path.name} (file id: {resp.id})")
    return resp.id


def launch(model: str, training_steps: int, learning_rate: float) -> str:
    train_path = settings.finetune_dir / "train.jsonl"
    eval_path = settings.finetune_dir / "eval.jsonl"
    if not train_path.exists():
        raise SystemExit("No train.jsonl found — run: python -m app.finetune.dataset")

    train_id = upload_file(train_path)
    eval_id = upload_file(eval_path) if eval_path.exists() else None

    client = get_client()
    job = with_retry(
        client.fine_tuning.jobs.create,
        model=model,
        training_files=[{"file_id": train_id, "weight": 1}],
        validation_files=[eval_id] if eval_id else None,
        hyperparameters={
            "training_steps": training_steps,
            "learning_rate": learning_rate,
        },
        auto_start=True,
    )
    print(f"✓ Fine-tuning job launched: {job.id} (base model: {model})")
    print("  Follow it here or with --status:", f"python -m app.finetune.train --status {job.id}")
    return job.id


def status(job_id: str, follow: bool = True) -> None:
    client = get_client()
    while True:
        job = with_retry(client.fine_tuning.jobs.get, job_id=job_id)
        print(f"Status: {job.status}")
        if job.status in ("SUCCESS", "FAILED", "CANCELLED", "FAILED_VALIDATION"):
            model_id = getattr(job, "fine_tuned_model", None)
            if job.status == "SUCCESS" and model_id:
                print(f"\n🎉 Your personal model is ready: {model_id}")
                print(f"Use it by setting in .env:\n  CHAT_MODEL={model_id}")
                print("Then restart the app, and compare quality with:")
                print(f"  python -m app.finetune.evaluate --finetuned {model_id}")
            return
        if not follow:
            return
        time.sleep(30)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default=DEFAULT_BASE_MODEL,
                        help="base model to fine-tune (default: %(default)s)")
    parser.add_argument("--steps", type=int, default=100, help="training steps")
    parser.add_argument("--lr", type=float, default=1e-4, help="learning rate")
    parser.add_argument("--status", metavar="JOB_ID", help="check/follow an existing job")
    args = parser.parse_args()

    if args.status:
        status(args.status)
    else:
        job_id = launch(args.model, args.steps, args.lr)
        status(job_id)


if __name__ == "__main__":
    main()
