"""Lightweight Prometheus metrics — stdlib only (no client dependency).

Exposes counters/gauges in the Prometheus text exposition format at ``/metrics``. Kept
dependency-free so the MVP stays installable anywhere; swap for ``prometheus_client`` in
production if you want histograms/summaries and multiprocess support.

Metrics emitted:
  pids_events_total{decision=...}   counter  detections processed, by pipeline outcome
  pids_alerts_total{criticality=...} counter alerts created, by criticality
  pids_notifications_total          counter  notifications dispatched
  pids_dedup_dropped_total          counter  events dropped as duplicates
"""
from __future__ import annotations

import threading
from collections import defaultdict


class MetricsRegistry:
    """Thread-safe labeled counters. Minimal by design."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # name -> {frozenset(labels.items()): value}
        self._counters: dict[str, dict[frozenset, float]] = defaultdict(dict)
        self._help: dict[str, str] = {}

    def register(self, name: str, help_text: str) -> None:
        self._help[name] = help_text

    def inc(self, name: str, amount: float = 1.0, **labels: str) -> None:
        key = frozenset(labels.items())
        with self._lock:
            bucket = self._counters[name]
            bucket[key] = bucket.get(key, 0.0) + amount

    def _fmt_labels(self, key: frozenset) -> str:
        if not key:
            return ""
        inner = ",".join(f'{k}="{v}"' for k, v in sorted(key))
        return "{" + inner + "}"

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            for name, buckets in sorted(self._counters.items()):
                if name in self._help:
                    lines.append(f"# HELP {name} {self._help[name]}")
                lines.append(f"# TYPE {name} counter")
                for key, value in sorted(buckets.items(), key=lambda kv: sorted(kv[0])):
                    lines.append(f"{name}{self._fmt_labels(key)} {value}")
        return "\n".join(lines) + "\n"


# Global registry used across the app.
REGISTRY = MetricsRegistry()
REGISTRY.register("pids_events_total", "Detections processed by the pipeline, by decision")
REGISTRY.register("pids_alerts_total", "Alerts created, by criticality")
REGISTRY.register("pids_notifications_total", "Notifications dispatched")
REGISTRY.register("pids_dedup_dropped_total", "Events dropped as duplicates")


def record_event(decision: str) -> None:
    REGISTRY.inc("pids_events_total", decision=decision)


def record_alert(criticality: str) -> None:
    REGISTRY.inc("pids_alerts_total", criticality=criticality)


def record_notifications(n: int) -> None:
    if n:
        REGISTRY.inc("pids_notifications_total", amount=float(n))


def record_dedup_dropped() -> None:
    REGISTRY.inc("pids_dedup_dropped_total")
