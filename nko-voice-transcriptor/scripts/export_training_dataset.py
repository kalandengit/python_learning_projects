#!/usr/bin/env python3
"""Export approved samples to speaker-disjoint AudioFolder train/test splits."""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path

from sqlalchemy import select

from app import db as db_module
from app.models import TrainingSample


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    db_module.init_db()
    assert db_module.SessionLocal is not None
    with db_module.SessionLocal() as db:
        rows = list(
            db.scalars(
                select(TrainingSample).where(
                    TrainingSample.status == "approved", TrainingSample.consent.is_(True)
                )
            )
        )
        writers = {}
        files = []
        try:
            for split in ("train", "test"):
                directory = args.output / split
                directory.mkdir(parents=True, exist_ok=True)
                handle = (directory / "metadata.csv").open("w", encoding="utf-8", newline="")
                writer = csv.writer(handle)
                writer.writerow(["file_name", "transcription", "language", "speaker_id"])
                writers[split] = writer
                files.append(handle)
            for row in rows:
                digest = hashlib.sha256(str(row.user_id).encode()).digest()[0]
                split = "test" if digest < 51 else "train"
                filename = f"sample-{row.id}.wav"
                shutil.copy2(row.audio_path, args.output / split / filename)
                writers[split].writerow(
                    [filename, row.corrected_text_latin, row.language, row.user_id]
                )
        finally:
            for handle in files:
                handle.close()
    print(f"Exported {len(rows)} approved samples to {args.output}")


if __name__ == "__main__":
    main()
