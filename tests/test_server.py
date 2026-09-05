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
            "telegram_send_location",
            "telegram_get_user_profile",
            "telegram_get_participant_permissions",
            "telegram_block_peer",
            "telegram_unblock_peer",
            "telegram_get_blocked_peers",
            "telegram_clear_chat",
            "telegram_send_and_verify",
            "telegram_run_test_suite",
            "telegram_execute_code",
        ]
        self.assertEqual(len(expected_tools), 54)
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

    def test_get_user_profile_phone_masking(self):
        import asyncio

        mock_client = AsyncMock()
        mock_user = MagicMock()
        mock_user.id = 99999
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.username = "testuser"
        mock_user.phone = "14155552671"
        mock_user.bot = False
        mock_user.verified = True
        mock_user.premium = True
        mock_user.scam = False
        mock_user.fake = False

        mock_full = MagicMock()
        mock_full.about = "Building cool agents"
        mock_full.common_chats_count = 3
        mock_full.blocked = False
        mock_full.pinned_msg_id = 100
        mock_full.bot_info = None

        mock_res = MagicMock()
        mock_res.full_user = mock_full
        mock_res.users = [mock_user]

        mock_client.get_input_entity = AsyncMock(return_value="mock_entity")
        mock_client.return_value = mock_res
        mock_client.__call__ = AsyncMock(return_value=mock_res)

        with patch.object(server.telegram_service, "_ensure_connected", AsyncMock(return_value=mock_client)):
            raw_result = asyncio.run(server.telegram_get_user_profile("testuser"))
            parsed = json.loads(raw_result)
            self.assertEqual(parsed["status"], "success")
            profile = parsed["user_profile"]
            self.assertEqual(profile["username"], "testuser")
            self.assertTrue(profile["is_premium"])
            self.assertTrue(profile["is_verified"])
            self.assertEqual(profile["about"], "Building cool agents")
            self.assertEqual(profile["phone"], "+14 ****** 2671")
            self.assertNotIn("555", profile["phone"])

    def test_get_participant_permissions(self):
        import asyncio
        from telethon import types

        mock_client = AsyncMock()
        mock_client.get_input_entity = AsyncMock(return_value="mock_peer")

        mock_participant = types.ChannelParticipantAdmin(
            user_id=123,
            promoted_by=456,
            date=None,
            admin_rights=types.ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=True,
                invite_users=True,
                pin_messages=True,
                add_admins=False,
                anonymous=False,
                manage_call=False,
                other=False,
            ),
            rank="Moderator",
        )
        mock_user = MagicMock()
        mock_user.id = 123
        mock_user.username = "mod_user"
        mock_user.first_name = "Mod"
        mock_user.bot = False

        mock_res = MagicMock()
        mock_res.participant = mock_participant
        mock_res.users = [mock_user]
        mock_client.return_value = mock_res

        with patch.object(server.telegram_service, "_ensure_connected", AsyncMock(return_value=mock_client)):
            raw_result = asyncio.run(server.telegram_get_participant_permissions("@testchannel", "mod_user"))
            parsed = json.loads(raw_result)
            self.assertEqual(parsed["status"], "success")
            perms = parsed["permissions"]
            self.assertEqual(perms["role"], "admin")
            self.assertTrue(perms["is_admin"])
            self.assertEqual(perms["rank"], "Moderator")
            self.assertTrue(perms["admin_rights"]["ban_users"])

    def test_block_peer(self):
        import asyncio

        mock_client = AsyncMock()
        mock_client.get_input_entity = AsyncMock(return_value="mock_peer")
        mock_client.return_value = True

        with patch.object(server.telegram_service, "_ensure_connected", AsyncMock(return_value=mock_client)):
            raw_result = asyncio.run(server.telegram_block_peer("@spambot"))
            parsed = json.loads(raw_result)
            self.assertTrue(parsed["success"])
            self.assertEqual(parsed["blocked_peer"], "@spambot")


if __name__ == "__main__":
    unittest.main()
