"""Unit tests for deduplication (pure, no DB)."""
from __future__ import annotations

import time

from app.dedup import InMemoryDedup, compute_idempotency_key


def test_same_detection_same_bucket_collapses():
    k1 = compute_idempotency_key(camera_id="c1", object_class="human", ts_epoch=1000.0, window_seconds=30)
    k2 = compute_idempotency_key(camera_id="c1", object_class="human", ts_epoch=1005.0, window_seconds=30)
    assert k1 == k2  # 1000 and 1005 fall in the same 30s bucket


def test_next_bucket_is_distinct():
    k1 = compute_idempotency_key(camera_id="c1", object_class="human", ts_epoch=1000.0, window_seconds=30)
    k2 = compute_idempotency_key(camera_id="c1", object_class="human", ts_epoch=1040.0, window_seconds=30)
    assert k1 != k2


def test_different_camera_distinct():
    k1 = compute_idempotency_key(camera_id="c1", object_class="human", ts_epoch=1000.0, window_seconds=30)
    k2 = compute_idempotency_key(camera_id="c2", object_class="human", ts_epoch=1000.0, window_seconds=30)
    assert k1 != k2


def test_in_memory_dedup_seen_semantics():
    d = InMemoryDedup()
    assert d.seen("k", ttl_seconds=60) is False  # first time -> not seen
    assert d.seen("k", ttl_seconds=60) is True  # second time -> seen


def test_in_memory_dedup_expiry():
    d = InMemoryDedup(purge_interval=0.0)  # purge every call for a deterministic expiry check
    assert d.seen("k", ttl_seconds=1) is False
    time.sleep(1.1)
    assert d.seen("k", ttl_seconds=1) is False  # expired -> treated as new again


def test_in_memory_dedup_throttled_purge_still_expires_by_ttl():
    # Even if the sweep is throttled, an expired key must not be reported as seen,
    # because seen() checks the per-key expiry directly.
    d = InMemoryDedup(purge_interval=3600.0)  # effectively never sweeps during the test
    assert d.seen("k", ttl_seconds=1) is False
    time.sleep(1.1)
    assert d.seen("k", ttl_seconds=1) is False


def test_in_memory_dedup_scales_without_quadratic_blowup():
    # Regression guard: 50k distinct keys must stay fast (amortized O(1) per call).
    d = InMemoryDedup()
    start = time.perf_counter()
    for i in range(50_000):
        assert d.seen(f"k-{i}", ttl_seconds=60) is False
    assert time.perf_counter() - start < 2.0  # generous; was ~8s with per-call full purge
