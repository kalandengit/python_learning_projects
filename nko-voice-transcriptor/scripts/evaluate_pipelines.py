#!/usr/bin/env python3
"""Compare pipeline hypotheses in JSONL using fixed WER/CER metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.metrics import error_rate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path, help="JSONL with reference and pipeline fields")
    parser.add_argument(
        "--pipelines",
        nargs="+",
        default=["mms", "mms_rag", "tuned_mms", "tuned_mms_rag_llm"],
    )
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8").splitlines()]
    result = {}
    for pipeline in args.pipelines:
        available = [row for row in rows if pipeline in row and "reference" in row]
        result[pipeline] = {
            "samples": len(available),
            "wer": sum(error_rate(row["reference"], row[pipeline]) for row in available)
            / max(1, len(available)),
            "cer": sum(
                error_rate(row["reference"], row[pipeline], characters=True)
                for row in available
            )
            / max(1, len(available)),
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
