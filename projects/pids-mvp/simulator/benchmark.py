"""Capacity benchmark for PIDS core components.

Measures throughput of the rule engine, the dedup layer, and the full ingestion pipeline
(in-process, SQLite). Use the numbers to size hardware — e.g. how many cameras a single
Raspberry Pi 5 node can serve. Run:

    python simulator/benchmark.py [--n 20000]

The rule engine and dedup are pure Python (CPU-bound), so their per-core rate scales roughly
with clock speed; apply a derating factor for a target CPU (see docs/RASPBERRY_PI5_DEPLOYMENT.md).
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import time
from datetime import datetime, timezone

# Ensure the backend package is importable when run from the repo root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

os.environ.setdefault("PIDS_DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/bench.db")
os.environ.setdefault("PIDS_SECRET_KEY", "bench")


def bench_rule_engine(n: int) -> float:
    from app.rule_engine import DEFAULT_RULES, RuleEngine, build_context

    engine = RuleEngine(rules=DEFAULT_RULES)
    ctxs = [
        build_context(object_class=c, confidence=0.9, zone="Parking", ts=datetime(2026, 7, 5, 23))
        for c in (["human", "dog", "truck", "cat", "vehicle"] * (n // 5 + 1))[:n]
    ]
    t0 = time.perf_counter()
    for c in ctxs:
        engine.evaluate(c)
    dt = time.perf_counter() - t0
    return n / dt


def bench_dedup(n: int) -> float:
    from app.dedup import InMemoryDedup, compute_idempotency_key

    d = InMemoryDedup()
    t0 = time.perf_counter()
    for i in range(n):
        key = compute_idempotency_key(
            camera_id="c1", object_class="human", ts_epoch=float(i), window_seconds=30, track_id=str(i)
        )
        d.seen(key, 30)
    dt = time.perf_counter() - t0
    return n / dt


def bench_pipeline(n: int) -> float:
    from app import models
    from app.database import SessionLocal, init_db
    from app.dedup import InMemoryDedup
    from app.notifications import default_service
    from app.pipeline import process_detection
    from app.schemas import DetectionEventIn
    from app.seed import seed

    init_db()
    db = SessionLocal()
    seed(db)
    cam = db.query(models.Camera).first()
    dedup, notifier = InMemoryDedup(), default_service()

    t0 = time.perf_counter()
    for i in range(n):
        payload = DetectionEventIn(
            camera_id=cam.id,
            object_class="human",
            confidence=0.9,
            ts=datetime.now(timezone.utc).replace(hour=23),
            track_id=f"t-{i}",  # unique -> avoids dedup, exercises the write path
        )
        process_detection(db, payload, dedup=dedup, notifier=notifier)
    dt = time.perf_counter() - t0
    db.close()
    return n / dt


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=20000)
    args = p.parse_args()

    print(f"Benchmarking on this host (n={args.n})...\n")
    re_rate = bench_rule_engine(args.n)
    dd_rate = bench_dedup(args.n)
    pl_rate = bench_pipeline(min(args.n, 5000))  # pipeline hits the DB; keep it bounded

    print(f"  Rule engine   : {re_rate:>12,.0f} evaluations/sec")
    print(f"  Dedup         : {dd_rate:>12,.0f} ops/sec")
    print(f"  Full pipeline : {pl_rate:>12,.0f} events/sec (SQLite, single process)")

    # Capacity translation: after NAR filtering, ~5 events/camera/day reach the pipeline;
    # peak bursts matter more than the daily average. Show a conservative headroom estimate.
    events_per_camera_peak = 0.05  # 1 event / 20s / camera at a busy perimeter
    cameras_supported = int(pl_rate / events_per_camera_peak)
    print(f"\n  Rough peak capacity (single process): ~{cameras_supported:,} cameras")
    print("  (Derate ~3-5x for a Raspberry Pi 5 vs a modern x86 core — see the Pi 5 doc.)")


if __name__ == "__main__":
    main()
