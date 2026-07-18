"""Command-line interface.

Usage:
    python -m app.cli ingest            # index every supported file in uploads/
    python -m app.cli ingest FILE...    # index specific files
    python -m app.cli watch             # keep watching uploads/ and index new files
    python -m app.cli list              # show what is in the knowledge base
    python -m app.cli delete FILE       # remove a file from the knowledge base
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from app.config import settings, setup_logging
from app.ingestion import indexer, router

logger = setup_logging()


def ingest_path(path: Path) -> bool:
    """Ingest one file; returns True on success. Failures are logged, never fatal."""
    try:
        doc = router.extract(path)
        n = indexer.index_document(doc)
        print(f"  ✓ {path.name}: {n} chunks (domain={doc.domain}, lang={doc.language})")
        return True
    except Exception as exc:  # noqa: BLE001 — one bad file must not stop the batch
        logger.error("Failed to ingest %s: %s", path, exc)
        print(f"  ✗ {path.name}: {exc}")
        return False


def _uploads_files() -> list[Path]:
    return sorted(
        p
        for p in settings.uploads_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in router.SUPPORTED_EXTS
    )


def cmd_ingest(files: list[str]) -> int:
    paths = [Path(f) for f in files] if files else _uploads_files()
    if not paths:
        print(f"No supported files found in {settings.uploads_dir}")
        return 0
    print(f"Ingesting {len(paths)} file(s)...")
    failures = sum(not ingest_path(p) for p in paths)
    print(f"Done: {len(paths) - failures} ok, {failures} failed.")
    return 1 if failures else 0


def cmd_watch() -> int:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    class Handler(FileSystemEventHandler):
        def on_created(self, event):  # type: ignore[override]
            if event.is_directory:
                return
            path = Path(str(event.src_path))
            if path.suffix.lower() not in router.SUPPORTED_EXTS:
                return
            time.sleep(2)  # let the copy finish before reading
            ingest_path(path)

    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    observer = Observer()
    observer.schedule(Handler(), str(settings.uploads_dir), recursive=True)
    observer.start()
    print(f"Watching {settings.uploads_dir} — drop files there. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return 0


def cmd_list() -> int:
    docs = indexer.list_documents()
    if not docs:
        print("Knowledge base is empty. Put files in uploads/ and run: python -m app.cli ingest")
        return 0
    for d in docs:
        print(f"  {d['source_file']:40s} {d['chunks']:4d} chunks  "
              f"domain={d['domain']}  lang={d['language']}")
    print(f"{len(docs)} document(s) indexed.")
    return 0


def cmd_delete(name: str) -> int:
    indexer.delete_document(name)
    print(f"Removed {name} from the knowledge base.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_ingest = sub.add_parser("ingest", help="index files (all of uploads/ by default)")
    p_ingest.add_argument("files", nargs="*", help="specific files to index")
    sub.add_parser("watch", help="watch uploads/ and index new files automatically")
    sub.add_parser("list", help="list indexed documents")
    p_del = sub.add_parser("delete", help="remove a document from the knowledge base")
    p_del.add_argument("file", help="source file name as shown by 'list'")

    args = parser.parse_args(argv)
    if args.command == "ingest":
        return cmd_ingest(args.files)
    if args.command == "watch":
        return cmd_watch()
    if args.command == "list":
        return cmd_list()
    if args.command == "delete":
        return cmd_delete(args.file)
    return 2


if __name__ == "__main__":
    sys.exit(main())
