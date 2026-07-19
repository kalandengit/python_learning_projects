import json
from unittest.mock import patch

import pytest

from app.config import settings
from app.finetune import dataset


def _write_log(tmp_path, n_good, n_bad=2):
    log = tmp_path / "chat_log.jsonl"
    lines = []
    for i in range(n_good):
        lines.append(json.dumps({"ts": f"T{i}", "question": f"Q{i}",
                                 "answer": f"A{i}", "rating": "good"}))
    for i in range(n_bad):
        lines.append(json.dumps({"ts": f"B{i}", "question": f"BQ{i}",
                                 "answer": f"BA{i}", "rating": "bad"}))
    lines.append(json.dumps({"ts": "U", "question": "UQ", "answer": "UA", "rating": None}))
    log.write_text("\n".join(lines) + "\n")


def test_build_uses_only_good_rated_examples(tmp_path):
    logs, ft = tmp_path / "logs", tmp_path / "ft"
    logs.mkdir(), (ft / "manual").mkdir(parents=True)
    _write_log(logs, n_good=30)
    with patch.object(settings, "logs_dir", logs), patch.object(settings, "finetune_dir", ft):
        train_path, eval_path, n_train, n_eval = dataset.build()
    assert n_train + n_eval == 30
    for line in train_path.read_text().splitlines():
        rec = json.loads(line)
        roles = [m["role"] for m in rec["messages"]]
        assert roles == ["system", "user", "assistant"]
        assert not rec["messages"][1]["content"].startswith("BQ")


def test_build_refuses_too_few_examples(tmp_path):
    logs, ft = tmp_path / "logs", tmp_path / "ft"
    logs.mkdir(), (ft / "manual").mkdir(parents=True)
    _write_log(logs, n_good=3)
    with patch.object(settings, "logs_dir", logs), patch.object(settings, "finetune_dir", ft):
        with pytest.raises(SystemExit, match="usable examples"):
            dataset.build()


def test_manual_examples_are_included_and_validated(tmp_path):
    logs, ft = tmp_path / "logs", tmp_path / "ft"
    logs.mkdir(), (ft / "manual").mkdir(parents=True)
    _write_log(logs, n_good=19)
    good = {"messages": [{"role": "user", "content": "q"},
                         {"role": "assistant", "content": "a"}]}
    bad = {"messages": [{"role": "assistant", "content": "a"},
                        {"role": "user", "content": "q"}]}  # wrong order
    (ft / "manual" / "mine.jsonl").write_text(
        json.dumps(good) + "\n" + json.dumps(bad) + "\n")
    with patch.object(settings, "logs_dir", logs), patch.object(settings, "finetune_dir", ft):
        _, _, n_train, n_eval = dataset.build()
    assert n_train + n_eval == 20  # 19 log + 1 valid manual, invalid one skipped


def test_example_jsonl_file_is_excluded(tmp_path):
    logs, ft = tmp_path / "logs", tmp_path / "ft"
    logs.mkdir(), (ft / "manual").mkdir(parents=True)
    _write_log(logs, n_good=20)
    (ft / "manual" / "example.jsonl").write_text(
        json.dumps({"messages": [{"role": "user", "content": "x"},
                                 {"role": "assistant", "content": "y"}]}) + "\n")
    with patch.object(settings, "logs_dir", logs), patch.object(settings, "finetune_dir", ft):
        _, _, n_train, n_eval = dataset.build()
    assert n_train + n_eval == 20
