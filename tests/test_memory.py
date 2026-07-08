from unittest.mock import patch, MagicMock

from langchain_core.messages import HumanMessage, AIMessage


def test_load_history_returns_messages():
    rows = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    with patch("memory.conversation.db.fetchall", return_value=rows):
        from memory.conversation import load_history

        msgs = load_history("fake-conv-id")

    assert len(msgs) == 2
    assert isinstance(msgs[0], HumanMessage)
    assert isinstance(msgs[1], AIMessage)
    assert msgs[0].content == "Hello"


def test_format_profile_for_prompt_empty():
    with patch("memory.user_profile.db.fetchall", return_value=[]):
        from memory.user_profile import format_profile_for_prompt

        result = format_profile_for_prompt()

    assert "No user profile" in result


def test_format_profile_for_prompt_with_data():
    rows = [{"category": "fact", "key": "name", "value": "Alice"}]
    with patch("memory.user_profile.db.fetchall", return_value=rows):
        from memory.user_profile import format_profile_for_prompt

        result = format_profile_for_prompt()

    assert "name" in result
    assert "Alice" in result
