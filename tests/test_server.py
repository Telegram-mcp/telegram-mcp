import unittest
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch
import server


class TestServerTools(unittest.TestCase):
    def test_registered_tools_count(self):
        tool_names = [t.name for t in server.mcp._tool_manager.list_tools()]
        expected_tools = [
            "telegram_status",
            "telegram_send_command",
            "telegram_send_message",
            "telegram_edit_message",
            "telegram_delete_messages",
            "telegram_forward_messages",
            "telegram_send_reaction",
            "telegram_send_poll",
            "telegram_send_album",
            "telegram_send_file",
            "telegram_download_media",
            "telegram_click_inline_button",
            "telegram_inline_query",
            "telegram_mark_chat_read",
            "telegram_list_dialogs",
            "telegram_search_messages",
            "telegram_get_chat_history",
            "telegram_get_message_context",
            "telegram_get_bot_info",
            "telegram_pin_message",
            "telegram_unpin_message",
            "telegram_save_draft",
            "telegram_schedule_message",
            "telegram_get_scheduled_messages",
            "telegram_delete_scheduled_messages",
            "telegram_get_pinned_messages",
            "telegram_mute_chat",
            "telegram_unmute_chat",
            "telegram_export_chat",
            "telegram_get_chat_members",
            "telegram_get_contacts",
            "telegram_resolve_peer",
            "telegram_wait_for",
            "telegram_get_web_app_url",
            "telegram_click_reply_button",
            "telegram_send_chat_action",
            "telegram_join_chat",
            "telegram_leave_chat",
            "telegram_vote_poll",
            "telegram_retract_vote",
            "telegram_search_media",
            "telegram_send_saved_message",
            "telegram_get_saved_messages",
            "telegram_download_profile_photo",
            "telegram_clear_chat",
            "telegram_send_and_verify",
            "telegram_run_test_suite",
            "telegram_execute_code",
        ]
        self.assertEqual(len(expected_tools), 48)
        for tool in expected_tools:
            self.assertIn(tool, tool_names, f"Missing tool: {tool}")

    def test_status_tool_phone_masking(self):
        import asyncio

        mock_client = AsyncMock()
        mock_me = MagicMock()
        mock_me.id = 12345
        mock_me.first_name = "Abhinav"
        mock_me.last_name = "M"
        mock_me.username = "abhinav"
        mock_me.phone = "919876543210"
        mock_client.get_me = AsyncMock(return_value=mock_me)

        with patch.dict(os.environ, {"TELEGRAM_SESSION": "fake_session"}), \
             patch.object(server.telegram_service, "get_client", AsyncMock(return_value=mock_client)):
            raw_result = asyncio.run(server.telegram_status())
            parsed = json.loads(raw_result)
            self.assertTrue(parsed["connected"])
            user = parsed["user"]
            self.assertEqual(user["phone"], "+91 ****** 3210")
            self.assertNotIn("987654", user["phone"])
            self.assertIn("rate_limiting", parsed)
            self.assertEqual(parsed["rate_limiting"]["flood_wait_events"], 0)


if __name__ == "__main__":
    unittest.main()
