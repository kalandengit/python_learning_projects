"""Rule engine — a small, dependency-free JSON Decision Model evaluator.

Rules are plain data (versionable, editable by non-developers, dry-runnable). Each rule is:

    {
      "name": "Humans at night are high criticality",
      "priority": 10,                       # lower number = evaluated first
      "conditions": [                        # ALL conditions must match (AND)
        {"field": "object_class", "op": "eq", "value": "human"},
        {"field": "hour", "op": "gte", "value": 22}
      ],
      "action": {"decision": "intrusion", "criticality": "high"}
    }

The engine evaluates a *context* (facts derived from an event) against an ordered list of rules
and returns the action of the first matching rule. If nothing matches, the default decision is
``ignore``. This mirrors the master prompt's §8 (deterministic, auditable, no LLM in the path).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

Decision = str  # "intrusion" | "false_positive" | "ignore"

_OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a is not None and a > b,
    "gte": lambda a, b: a is not None and a >= b,
    "lt": lambda a, b: a is not None and a < b,
    "lte": lambda a, b: a is not None and a <= b,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "between": lambda a, b: a is not None and b[0] <= a <= b[1],
}

_VALID_DECISIONS = {"intrusion", "false_positive", "ignore"}
_VALID_CRITICALITY = {"low", "medium", "high", "critical"}


@dataclass
class Outcome:
    decision: Decision
    criticality: str | None
    matched_rule: str | None
    reason: str

    def is_intrusion(self) -> bool:
        return self.decision == "intrusion"


@dataclass
class RuleEngine:
    """Evaluate detection contexts against an ordered rule set."""

    rules: list[dict] = field(default_factory=list)
    default_decision: Decision = "ignore"

    def _sorted(self) -> list[dict]:
        return sorted(
            (r for r in self.rules if r.get("enabled", True)),
            key=lambda r: r.get("priority", 100),
        )

    @staticmethod
    def _condition_matches(cond: dict, ctx: dict) -> bool:
        op = _OPERATORS.get(cond["op"])
        if op is None:
            raise ValueError(f"unknown operator: {cond['op']!r}")
        return bool(op(ctx.get(cond["field"]), cond["value"]))

    def evaluate(self, ctx: dict) -> Outcome:
        """Return the action of the first rule whose conditions all match."""
        for rule in self._sorted():
            conditions = rule.get("conditions", [])
            if all(self._condition_matches(c, ctx) for c in conditions):
                action = rule.get("action", {})
                decision = action.get("decision", "ignore")
                if decision not in _VALID_DECISIONS:
                    raise ValueError(f"invalid decision {decision!r} in rule {rule.get('name')!r}")
                return Outcome(
                    decision=decision,
                    criticality=action.get("criticality"),
                    matched_rule=rule.get("name"),
                    reason=f"matched rule {rule.get('name')!r}",
                )
        return Outcome(
            decision=self.default_decision,
            criticality=None,
            matched_rule=None,
            reason="no rule matched; default applied",
        )

    def dry_run(self, contexts: list[dict]) -> list[Outcome]:
        """Evaluate many historical contexts without side effects (simulation)."""
        return [self.evaluate(c) for c in contexts]


def build_context(
    *,
    object_class: str,
    confidence: float,
    zone: str | None = None,
    ts: datetime | None = None,
    security_level: int | None = None,
    extra: dict | None = None,
) -> dict:
    """Derive rule-engine facts from an event. ``hour``/``weekday`` are computed from ``ts``."""
    ts = ts or datetime.now()
    ctx: dict[str, Any] = {
        "object_class": object_class,
        "confidence": confidence,
        "zone": zone,
        "hour": ts.hour,
        "weekday": ts.weekday(),  # 0 = Monday
        "is_night": ts.hour >= 22 or ts.hour < 6,
        "security_level": security_level,
    }
    if extra:
        ctx.update(extra)
    return ctx


def validate_rule(rule: dict) -> None:
    """Raise ValueError if a rule is malformed (used before persisting/activating)."""
    if "action" not in rule:
        raise ValueError("rule missing 'action'")
    action = rule["action"]
    if action.get("decision") not in _VALID_DECISIONS:
        raise ValueError(f"action.decision must be one of {sorted(_VALID_DECISIONS)}")
    crit = action.get("criticality")
    if crit is not None and crit not in _VALID_CRITICALITY:
        raise ValueError(f"action.criticality must be one of {sorted(_VALID_CRITICALITY)}")
    for cond in rule.get("conditions", []):
        if cond.get("op") not in _OPERATORS:
            raise ValueError(f"unknown operator {cond.get('op')!r}")
        if "field" not in cond or "value" not in cond:
            raise ValueError("each condition needs 'field', 'op', and 'value'")


# A sensible default rule set matching the master prompt's business-intelligence examples.
DEFAULT_RULES: list[dict] = [
    {
        "name": "Ignore low-confidence detections",
        "priority": 5,
        "conditions": [{"field": "confidence", "op": "lt", "value": 0.4}],
        "action": {"decision": "ignore"},
    },
    {
        "name": "Dogs are ignored",
        "priority": 10,
        "conditions": [{"field": "object_class", "op": "eq", "value": "dog"}],
        "action": {"decision": "ignore"},
    },
    {
        "name": "Vehicle in parking at night triggers alarm",
        "priority": 20,
        "conditions": [
            {"field": "object_class", "op": "in", "value": ["vehicle", "car", "truck"]},
            {"field": "zone", "op": "eq", "value": "Parking"},
            {"field": "is_night", "op": "eq", "value": True},
        ],
        "action": {"decision": "intrusion", "criticality": "high"},
    },
    {
        "name": "Human after 22:00 is high criticality",
        "priority": 30,
        "conditions": [
            {"field": "object_class", "op": "eq", "value": "human"},
            {"field": "hour", "op": "gte", "value": 22},
        ],
        "action": {"decision": "intrusion", "criticality": "high"},
    },
    {
        "name": "Any human is an intrusion (medium)",
        "priority": 100,
        "conditions": [{"field": "object_class", "op": "eq", "value": "human"}],
        "action": {"decision": "intrusion", "criticality": "medium"},
    },
]
