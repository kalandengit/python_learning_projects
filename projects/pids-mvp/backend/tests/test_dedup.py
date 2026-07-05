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
    d = InMemoryDedup()
    assert d.seen("k", ttl_seconds=1) is False
    time.sleep(1.1)
    assert d.seen("k", ttl_seconds=1) is False  # expired -> treated as new again
