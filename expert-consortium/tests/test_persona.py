from app.rag.persona import CONSORTIUM_PROMPT, build_messages


def test_prompt_mentions_all_four_experts():
    for term in ("Law & Courts", "N'Ko", "Islamic sciences", "Computer Science"):
        assert term in CONSORTIUM_PROMPT


def test_messages_include_context_and_citation_format():
    msgs = build_messages("What did the court decide?",
                          [("ruling.pdf", "The court dismissed the appeal.")])
    assert msgs[0]["role"] == "system"
    user = msgs[-1]["content"]
    assert "[ruling.pdf]" in user
    assert "The court dismissed the appeal." in user
    assert "What did the court decide?" in user


def test_messages_without_context_flag_missing_knowledge():
    msgs = build_messages("Unknown topic?", [])
    assert "No relevant excerpts" in msgs[-1]["content"]


def test_history_is_inserted_between_system_and_user():
    history = [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]
    msgs = build_messages("next?", [("a.txt", "text")], history)
    assert [m["role"] for m in msgs] == ["system", "user", "assistant", "user"]
