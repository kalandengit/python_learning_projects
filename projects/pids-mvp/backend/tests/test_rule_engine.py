"""Unit tests for the rule engine (pure, no DB)."""
from __future__ import annotations

from datetime import datetime

import pytest

from app.rule_engine import DEFAULT_RULES, RuleEngine, build_context, validate_rule


@pytest.fixture()
def engine():
    return RuleEngine(rules=DEFAULT_RULES)


def test_low_confidence_is_ignored(engine):
    ctx = build_context(object_class="human", confidence=0.2, ts=datetime(2026, 7, 5, 14))
    outcome = engine.evaluate(ctx)
    assert outcome.decision == "ignore"
    assert outcome.matched_rule == "Ignore low-confidence detections"


def test_dog_is_ignored(engine):
    ctx = build_context(object_class="dog", confidence=0.9, ts=datetime(2026, 7, 5, 14))
    assert engine.evaluate(ctx).decision == "ignore"


def test_human_daytime_is_medium_intrusion(engine):
    ctx = build_context(object_class="human", confidence=0.9, ts=datetime(2026, 7, 5, 14))
    outcome = engine.evaluate(ctx)
    assert outcome.is_intrusion()
    assert outcome.criticality == "medium"


def test_human_at_night_is_high(engine):
    ctx = build_context(object_class="human", confidence=0.9, ts=datetime(2026, 7, 5, 23))
    outcome = engine.evaluate(ctx)
    assert outcome.is_intrusion()
    assert outcome.criticality == "high"
    assert outcome.matched_rule == "Human after 22:00 is high criticality"


def test_vehicle_in_parking_at_night_triggers_alarm(engine):
    ctx = build_context(object_class="truck", confidence=0.8, zone="Parking", ts=datetime(2026, 7, 5, 2))
    outcome = engine.evaluate(ctx)
    assert outcome.is_intrusion()
    assert outcome.criticality == "high"


def test_priority_ordering_low_confidence_wins_over_intrusion(engine):
    # Low confidence + human at night: the priority-5 ignore rule must win.
    ctx = build_context(object_class="human", confidence=0.1, ts=datetime(2026, 7, 5, 23))
    assert engine.evaluate(ctx).decision == "ignore"


def test_no_rule_matches_defaults_to_ignore(engine):
    ctx = build_context(object_class="cat", confidence=0.9, ts=datetime(2026, 7, 5, 14))
    assert engine.evaluate(ctx).decision == "ignore"


def test_dry_run_is_side_effect_free(engine):
    contexts = [
        build_context(object_class="human", confidence=0.9, ts=datetime(2026, 7, 5, 23)),
        build_context(object_class="dog", confidence=0.9, ts=datetime(2026, 7, 5, 23)),
    ]
    outcomes = engine.dry_run(contexts)
    assert [o.decision for o in outcomes] == ["intrusion", "ignore"]


def test_validate_rule_rejects_bad_decision():
    with pytest.raises(ValueError):
        validate_rule({"action": {"decision": "boom"}})


def test_validate_rule_rejects_unknown_operator():
    with pytest.raises(ValueError):
        validate_rule({"conditions": [{"field": "x", "op": "??", "value": 1}], "action": {"decision": "ignore"}})
