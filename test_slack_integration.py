"""Tests for slack_integration.py and the slack_skill in logic.py."""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, "/root/workspace/whatsapp_bot")

from slack_integration import (
    get_recent_action_items,
    _extract_channels,
    _extract_messages,
    TASK_PATTERNS,
)
from logic import (
    handle_message,
    slack_skill,
    _matches_slack,
    SLACK_KEYWORDS,
)


# ── TASK_PATTERNS regex tests ─────────────────────────────────────────────────────────

class TestTaskPatterns:
    def test_matches_todo(self):
        assert TASK_PATTERNS.search("TODO: fix the bug")

    def test_matches_task(self):
        assert TASK_PATTERNS.search("This is a task for John")

    def test_matches_action_item(self):
        assert TASK_PATTERNS.search("action item: review PR")

    def test_matches_da_fare(self):
        assert TASK_PATTERNS.search("Da fare: aggiornare il documento")

    def test_matches_check_emoji_text(self):
        assert TASK_PATTERNS.search(":white_check_mark: deploy v2")

    def test_matches_unicode_check(self):
        assert TASK_PATTERNS.search("✅ done with the report")

    def test_no_match(self):
        assert TASK_PATTERNS.search("Hello everyone, good morning!") is None

    def test_case_insensitive(self):
        assert TASK_PATTERNS.search("TODO update docs")
        assert TASK_PATTERNS.search("Todo update docs")
        assert TASK_PATTERNS.search("todo update docs")


# ── _extract_channels tests ───────────────────────────────────────────────────────────

class TestExtractChannels:
    def test_flat_dict(self):
        resp = {"channels": [{"id": "C1", "name": "general"}]}
        assert _extract_channels(resp) == [{"id": "C1", "name": "general"}]

    def test_nested_data_dict(self):
        resp = {"data": {"channels": [{"id": "C2", "name": "random"}]}}
        assert _extract_channels(resp) == [{"id": "C2", "name": "random"}]

    def test_object_with_data_attr(self):
        obj = MagicMock()
        obj.data = {"channels": [{"id": "C3", "name": "dev"}]}
        assert _extract_channels(obj) == [{"id": "C3", "name": "dev"}]

    def test_empty_response(self):
        assert _extract_channels({}) == []

    def test_non_list_channels(self):
        assert _extract_channels({"channels": "not a list"}) == []


# ── _extract_messages tests ───────────────────────────────────────────────────────────

class TestExtractMessages:
    def test_flat_dict(self):
        resp = {"messages": [{"text": "hello", "user": "U1"}]}
        assert _extract_messages(resp) == [{"text": "hello", "user": "U1"}]

    def test_nested_data_dict(self):
        resp = {"data": {"messages": [{"text": "hi"}]}}
        assert _extract_messages(resp) == [{"text": "hi"}]

    def test_empty(self):
        assert _extract_messages({}) == []


# ── get_recent_action_items tests ─────────────────────────────────────────────────────

class TestGetRecentActionItems:
    def test_missing_api_key_returns_empty(self):
        with patch.dict(os.environ, {}, clear=True):
            result = get_recent_action_items()
            assert result == []

    @patch("slack_integration.Composio")
    def test_no_channels_returns_empty(self, mock_composio_cls):
        mock_client = MagicMock()
        mock_composio_cls.return_value = mock_client
        mock_client.tools.execute.return_value = {"channels": []}

        with patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-key"}):
            result = get_recent_action_items()
        assert result == []

    @patch("slack_integration.Composio")
    def test_finds_action_items(self, mock_composio_cls):
        mock_client = MagicMock()
        mock_composio_cls.return_value = mock_client

        def side_effect(action_name, arguments):
            if action_name == "SLACK_LIST_CONVERSATIONS":
                return {"channels": [{"id": "C1", "name": "general"}]}
            elif action_name == "SLACK_FETCH_CONVERSATION_HISTORY":
                return {
                    "messages": [
                        {"text": "TODO: deploy to prod", "user": "U1"},
                        {"text": "good morning everyone", "user": "U2"},
                        {"text": "action item: review the PR", "user": "U3"},
                    ]
                }
            return {}

        mock_client.tools.execute.side_effect = side_effect

        with patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-key"}):
            result = get_recent_action_items()

        assert len(result) == 2
        assert result[0]["channel"] == "general"
        assert "TODO" in result[0]["text"]
        assert result[1]["text"] == "action item: review the PR"

    @patch("slack_integration.Composio")
    def test_multiple_channels(self, mock_composio_cls):
        mock_client = MagicMock()
        mock_composio_cls.return_value = mock_client

        call_count = 0

        def side_effect(action_name, arguments):
            nonlocal call_count
            if action_name == "SLACK_LIST_CONVERSATIONS":
                return {
                    "channels": [
                        {"id": "C1", "name": "general"},
                        {"id": "C2", "name": "engineering"},
                    ]
                }
            elif action_name == "SLACK_FETCH_CONVERSATION_HISTORY":
                call_count += 1
                if arguments["channel"] == "C1":
                    return {"messages": [{"text": "task: fix login bug", "user": "U1"}]}
                else:
                    return {"messages": [{"text": "✅ deploy done", "user": "U2"}]}
            return {}

        mock_client.tools.execute.side_effect = side_effect

        with patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-key"}):
            result = get_recent_action_items()

        assert len(result) == 2
        assert result[0]["channel"] == "general"
        assert result[1]["channel"] == "engineering"
        assert call_count == 2

    @patch("slack_integration.Composio")
    def test_channel_history_error_continues(self, mock_composio_cls):
        mock_client = MagicMock()
        mock_composio_cls.return_value = mock_client

        def side_effect(action_name, arguments):
            if action_name == "SLACK_LIST_CONVERSATIONS":
                return {
                    "channels": [
                        {"id": "C1", "name": "broken"},
                        {"id": "C2", "name": "working"},
                    ]
                }
            elif action_name == "SLACK_FETCH_CONVERSATION_HISTORY":
                if arguments["channel"] == "C1":
                    raise Exception("channel not found")
                return {"messages": [{"text": "todo: write tests", "user": "U1"}]}
            return {}

        mock_client.tools.execute.side_effect = side_effect

        with patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-key"}):
            result = get_recent_action_items()

        assert len(result) == 1
        assert result[0]["channel"] == "working"

    @patch("slack_integration.Composio")
    def test_api_exception_returns_empty(self, mock_composio_cls):
        mock_client = MagicMock()
        mock_composio_cls.return_value = mock_client
        mock_client.tools.execute.side_effect = Exception("API down")

        with patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-key"}):
            result = get_recent_action_items()
        assert result == []

    @patch("slack_integration.Composio")
    def test_passes_correct_params(self, mock_composio_cls):
        mock_client = MagicMock()
        mock_composio_cls.return_value = mock_client
        mock_client.tools.execute.return_value = {"channels": []}

        with patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-key"}):
            get_recent_action_items()

        call_args = mock_client.tools.execute.call_args
        assert call_args[0][0] == "SLACK_LIST_CONVERSATIONS"
        params = call_args[1]["arguments"]
        assert params["types"] == "public_channel"
        assert params["exclude_archived"] is True

    @patch("slack_integration.Composio")
    def test_no_task_messages_returns_empty(self, mock_composio_cls):
        mock_client = MagicMock()
        mock_composio_cls.return_value = mock_client

        def side_effect(action_name, arguments):
            if action_name == "SLACK_LIST_CONVERSATIONS":
                return {"channels": [{"id": "C1", "name": "general"}]}
            elif action_name == "SLACK_FETCH_CONVERSATION_HISTORY":
                return {
                    "messages": [
                        {"text": "good morning", "user": "U1"},
                        {"text": "how is everyone?", "user": "U2"},
                    ]
                }
            return {}

        mock_client.tools.execute.side_effect = side_effect

        with patch.dict(os.environ, {"COMPOSIO_API_KEY": "test-key"}):
            result = get_recent_action_items()
        assert result == []


# ── SLACK_KEYWORDS / _matches_slack tests ───────────────────────────────────────────

class TestSlackKeywords:
    def test_keywords_set(self):
        assert "slack" in SLACK_KEYWORDS
        assert "task" in SLACK_KEYWORDS
        assert "todo" in SLACK_KEYWORDS
        assert "messaggi" in SLACK_KEYWORDS

    def test_matches_slack(self):
        assert _matches_slack("show me slack tasks") is True
        assert _matches_slack("my todo list") is True
        assert _matches_slack("messaggi recenti") is True

    def test_no_match(self):
        assert _matches_slack("hello world") is False


# ── slack_skill tests ─────────────────────────────────────────────────────────────

class TestSlackSkill:
    @patch("logic.get_recent_action_items")
    def test_no_items_message(self, mock_get):
        mock_get.return_value = []
        result = slack_skill("show slack tasks")
        assert "Slack Skill" in result
        assert "No action items" in result

    @patch("logic.get_recent_action_items")
    def test_items_formatted(self, mock_get):
        mock_get.return_value = [
            {"channel": "general", "text": "TODO: fix login", "user": "U1"},
            {"channel": "engineering", "text": "task: write docs", "user": "U2"},
        ]
        result = slack_skill("show slack tasks")
        assert "Slack Skill" in result
        assert "#general" in result
        assert "TODO: fix login" in result
        assert "#engineering" in result
        assert "Action items found (2)" in result

    @patch("logic.get_recent_action_items")
    def test_long_message_truncated(self, mock_get):
        long_text = "TODO: " + "x" * 300
        mock_get.return_value = [
            {"channel": "general", "text": long_text, "user": "U1"},
        ]
        result = slack_skill("tasks")
        assert "..." in result
        assert len(result) < len(long_text) + 200

    @patch("logic.get_recent_action_items")
    def test_includes_user_query(self, mock_get):
        mock_get.return_value = []
        result = slack_skill("show me my todo items")
        assert "show me my todo items" in result


# ── handle_message routing tests ──────────────────────────────────────────────────────

class TestHandleMessageSlackRouting:
    @patch("logic.get_recent_action_items")
    def test_routes_to_slack_for_task(self, mock_get):
        mock_get.return_value = []
        reply = handle_message("show me my task list")
        assert "Slack Skill" in reply

    @patch("logic.get_recent_action_items")
    def test_routes_to_slack_for_todo(self, mock_get):
        mock_get.return_value = []
        reply = handle_message("what's on my todo")
        assert "Slack Skill" in reply

    @patch("logic.get_recent_action_items")
    def test_routes_to_slack_for_slack(self, mock_get):
        mock_get.return_value = []
        reply = handle_message("check slack")
        assert "Slack Skill" in reply

    @patch("logic.get_recent_action_items")
    def test_routes_to_slack_for_messaggi(self, mock_get):
        mock_get.return_value = []
        reply = handle_message("messaggi recenti")
        assert "Slack Skill" in reply

    def test_faq_still_takes_priority(self):
        reply = handle_message("I need help with a task")
        assert "FAQ Skill" in reply

    def test_default_reply_updated(self):
        reply = handle_message("random gibberish xyz")
        assert "didn't understand" in reply
