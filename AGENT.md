# AGENT.md - Telegram MCP Server Guide (Python + Telethon)

> [!WARNING]
> **Disclaimer**: This project is an independent open-source tool and is **not affiliated with, authorized, maintained, sponsored, or endorsed by Telegram FZ-LLC, Telegram Messenger Inc., or any of their affiliates**. "Telegram" is a registered trademark of its respective owners.

This guide documents the architecture, setup, development workflow, and conventions for the `telegram-mcp` project.

---

## 1. Project Overview

`telegram-mcp` is a Model Context Protocol (MCP) server built with Python (`mcp` / `MCPServer`) and `Telethon`. It enables AI coding agents to interact with, test, and verify Telegram bots. It provides both high-level testing tools and a direct Python code execution sandbox (`telegram_execute_code`) for arbitrary MTProto automation.

---

## 🛡️ Critical Environment Matching Rule

- **Test Server (`TELEGRAM_TEST_MODE=true`)**: The target bot **MUST** also be on the **Test Server** (created via `@BotFather` inside the test server, using endpoint `https://api.telegram.org/bot<TOKEN>/test/`).
- **Production Server (`TELEGRAM_TEST_MODE=false`)**: The target bot **MUST** be on the **Production Server**.
- **Isolation**: Test Server and Production Server are completely separate. A test client cannot message a production bot (and vice versa).
- **Recommendation**: Always use or recommend the **Test Server** for testing during active development to eliminate any risk to the developer's main personal account.

---

## 2. Directory Structure

```
/root/bot-mcp
├── server.py              # Main MCP server entrypoint and tool definitions
├── telegram_service.py    # Telethon MTProto client wrapper and interaction methods
├── login.py               # Interactive CLI helper for Telegram authentication
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── AGENT.md               # AI agent reference documentation
├── CHANGELOG.md           # Project history in Asia/Kolkata timezone
├── CONTRIBUTING.md        # Contribution guide
└── LICENSE                # MIT License
```

---

## 3. Development Commands

- **Install Dependencies**: `pip install -r requirements.txt`
- **Install Dev / Test Dependencies**: `pip install -r requirements-dev.txt`
- **Run Unit Tests**: `python3 -m pytest tests -v` or `python3 -m unittest discover -s tests`
- **Login / Generate Session**: `python3 login.py`
- **Run MCP Server**: `python3 server.py`

---

## 3.1 Session Safety

The server uses a process-level file lock (`/tmp/telegram-mcp.lock`) to prevent multiple instances from connecting with the same Telegram session simultaneously. If a second instance starts, it will fail immediately with a clear error instead of destroying the session.

- **Never run two `server.py` processes at the same time.** The lock prevents it, but be aware.
- If you see `AuthKeyDuplicatedError`, the session is permanently dead. Re-login with `python3 login.py`.
- The server validates the session eagerly on startup and disconnects cleanly on shutdown.

---

## 4. MCP Tools Reference

The server exposes the following tools:

1. `telegram_status`
   - **Arguments**: None
   - **Usage**: Checks connection health, configuration flags, and active user metadata with masked phone number for privacy.

2. `telegram_send_command`
   - **Arguments**: `bot_username`, `command`, `wait_response` (default: `True`), `timeout_seconds` (default: `10`)
   - **Usage**: Sends a `/command` to the bot and returns the reply with inline keyboard buttons.

3. `telegram_send_message`
   - **Arguments**: `bot_username`, `text`, `reply_to_msg_id?`, `parse_mode?` (default: `"md"`), `wait_response` (default: `True`), `timeout_seconds` (default: `10`)
   - **Usage**: Sends arbitrary text messages with Markdown/HTML formatting support.

4. `telegram_edit_message`
   - **Arguments**: `bot_username`, `message_id`, `new_text`, `parse_mode?` (default: `"md"`)
   - **Usage**: Edits a previously sent message by ID.

5. `telegram_delete_messages`
   - **Arguments**: `bot_username`, `message_ids`, `revoke?` (default: `True`)
   - **Usage**: Deletes one or more messages by ID.

6. `telegram_forward_messages`
   - **Arguments**: `to_chat`, `from_chat`, `message_ids`
   - **Usage**: Forwards messages from one chat to another.

7. `telegram_send_reaction`
   - **Arguments**: `bot_username`, `message_id`, `reaction`
   - **Usage**: Sends an emoji reaction (👍, 🔥, ❤️, etc.) to a message.

8. `telegram_send_poll`
   - **Arguments**: `bot_username`, `question`, `options`, `is_quiz?` (default: `False`), `correct_option_id?`
   - **Usage**: Creates and sends native Telegram polls or quizzes.

9. `telegram_mark_chat_read`
   - **Arguments**: `bot_username`, `max_id?`
   - **Usage**: Marks messages in a chat as read.

10. `telegram_list_dialogs`
    - **Arguments**: `limit?` (default: `20`)
    - **Usage**: Lists recent chats, groups, bots, and channels with unread counts and last messages.

11. `telegram_search_messages`
    - **Arguments**: `bot_username`, `query`, `limit?` (default: `20`)
    - **Usage**: Searches message history within a specific chat by keyword.

12. `telegram_click_inline_button`
    - **Arguments**: `bot_username`, `message_id?`, `button_text?`, `button_index?`, `wait_update` (default: `True`)
    - **Usage**: Triggers callback queries on inline keyboard buttons attached to a bot message.

13. `telegram_send_file`
    - **Arguments**: `bot_username`, `file_path`, `caption?`, `reply_to_msg_id?`, `voice_note?` (default: `False`), `wait_response` (default: `True`), `timeout_seconds` (default: `15`)
    - **Usage**: Sends files, images, voice notes (circular), or documents to the bot.

14. `telegram_download_media`
    - **Arguments**: `bot_username`, `message_id`, `output_dir?`
    - **Usage**: Downloads media (photos, documents, audio) attached to a bot's message.

15. `telegram_inline_query`
    - **Arguments**: `bot_username`, `query`
    - **Usage**: Simulates typing `@bot query` in inline mode and inspects returned results.

16. `telegram_send_and_verify`
    - **Arguments**: `bot_username`, `input_text`, `expected_contains`, `timeout_seconds` (default: `10`)
    - **Usage**: Single-step assertion check.

17. `telegram_run_test_suite`
    - **Arguments**: `bot_username`, `steps`
    - **Usage**: Executes multi-step test workflows with `sleep`, `assert_reply`, `send_file`, and `click_button`.

18. `telegram_execute_code` *(Full Control Sandbox)*
    - **Arguments**: `code` (string), `timeout_seconds` (default: `30`)
    - **Environment Injected**:
      - `client`: Live authenticated `Telethon.TelegramClient` instance (supports raw MTProto functions, event listeners, updates, etc.)
      - `service` / `telegram_service`: `TelegramService` instance
      - `events`: `telethon.events`
      - `functions`, `types`: `telethon.tl.functions`, `telethon.tl.types`
      - `asyncio`, `json`, `os`, `time`
    - **Returns**: Captured `stdout`, `stderr`, `return_value`, `duration_seconds`, and error stack traces.

19. `telegram_get_chat_history`
    - **Arguments**: `bot_username`, `limit` (default: `10`)
    - **Usage**: Retrieves recent messages, media info, and button metadata.

20. `telegram_clear_chat`
    - **Arguments**: `bot_username`
    - **Usage**: Deletes dialog history for clean testing states.

21. `telegram_get_bot_info`
    - **Arguments**: `bot_username`
    - **Usage**: Retrieves full bot profile information including title, description, about text, and registered commands.

22. `telegram_pin_message`
    - **Arguments**: `bot_username`, `message_id`, `notify?` (default: `False`)
    - **Usage**: Pins a message in the chat with the bot or group.

23. `telegram_unpin_message`
    - **Arguments**: `bot_username`, `message_id?`
    - **Usage**: Unpins a specific message, or all pinned messages if omitted.

24. `telegram_get_message_context`
    - **Arguments**: `bot_username`, `message_id`, `limit_before?` (default: `5`), `limit_after?` (default: `5`)
    - **Usage**: Fetches surrounding conversation context around a specific message ID.

25. `telegram_send_album`
    - **Arguments**: `bot_username`, `file_paths`, `caption?`
    - **Usage**: Sends multiple photos/files as a grouped album in a single message.

26. `telegram_save_draft`
    - **Arguments**: `bot_username`, `text`, `reply_to_msg_id?`
    - **Usage**: Saves an uncommitted draft into the chat input field without sending it.

27. `telegram_schedule_message`
    - **Arguments**: `bot_username`, `text`, `schedule_in_seconds?`, `schedule_date_iso?`
    - **Usage**: Schedules a message to be automatically delivered in the future.

28. `telegram_get_scheduled_messages`
    - **Arguments**: `bot_username`
    - **Usage**: Retrieves all pending scheduled messages queued in a chat.

29. `telegram_delete_scheduled_messages`
    - **Arguments**: `bot_username`, `message_ids`
    - **Usage**: Cancels or deletes scheduled messages before delivery.

30. `telegram_get_pinned_messages`
    - **Arguments**: `bot_username`, `limit?` (default: `10`)
    - **Usage**: Directly retrieves pinned messages in any chat, bot, or channel.

31. `telegram_mute_chat`
    - **Arguments**: `bot_username`, `duration_seconds?`
    - **Usage**: Mutes chat notifications for a specified duration or permanently.

32. `telegram_unmute_chat`
    - **Arguments**: `bot_username`
    - **Usage**: Unmutes notifications for a chat or channel.

33. `telegram_export_chat`
    - **Arguments**: `bot_username`, `limit?` (default: `50`), `format?` (`"markdown"` or `"json"`)
    - **Usage**: Exports formatted conversation transcripts optimized for AI summarization and reasoning.

34. `telegram_get_chat_members`
    - **Arguments**: `bot_username`, `limit?` (default: `50`)
    - **Usage**: Lists group or channel participants with their names, IDs, and bot status.

35. `telegram_get_contacts`
    - **Arguments**: `query?`, `limit?` (default: `50`)
    - **Usage**: Retrieves saved Telegram contacts with privacy-masked phone numbers.

36. `telegram_resolve_peer`
    - **Arguments**: `peer`
    - **Usage**: Resolves any entity (username, phone, invite link, ID) into full metadata and classification.

37. `telegram_wait_for`
    - **Arguments**: `bot_username`, `text_contains?`, `after_message_id?`, `target_message_id?`, `wait_for_edit?` (default: `False`), `timeout_seconds` (default: `30`), `poll_interval` (default: `1.0`)
    - **Usage**: Explicitly waits for an asynchronous bot response, incoming text match, or message edit/progress update.

38. `telegram_get_web_app_url`
    - **Arguments**: `bot_username`, `message_id?`, `button_text?`, `button_index?`
    - **Usage**: Extracts the authenticated Web App launch URL from a Telegram Mini App button for browser/Playwright testing.

39. `telegram_click_reply_button`
    - **Arguments**: `bot_username`, `button_text?`, `button_index?`, `wait_response?` (default: `True`), `timeout_seconds` (default: `15`)
    - **Usage**: Clicks buttons in persistent bottom reply keyboards (`ReplyKeyboardMarkup`).

40. `telegram_send_chat_action`
    - **Arguments**: `bot_username`, `action?` (default: `"typing"`)
    - **Usage**: Broadcasts chat presence indicators (`"typing"`, `"upload_photo"`, `"record_video"`, etc.).

41. `telegram_join_chat`
    - **Arguments**: `chat_identifier`
    - **Usage**: Joins a public channel/supergroup via `@username` or private chat via invite link (`t.me/+...`).

42. `telegram_leave_chat`
    - **Arguments**: `chat_identifier`
    - **Usage**: Leaves a channel or supergroup by username or ID.

43. `telegram_vote_poll`
    - **Arguments**: `bot_username`, `message_id`, `option_index`
    - **Usage**: Casts a vote on single-choice or multi-choice native Telegram polls or quizzes.

44. `telegram_retract_vote`
    - **Arguments**: `bot_username`, `message_id`
    - **Usage**: Retracts / revokes an existing vote on a poll.

45. `telegram_search_media`
    - **Arguments**: `bot_username`, `media_type?` (`"photo"`, `"document"`, `"video"`, `"voice"`, `"audio"`, `"url"`, `"gif"`), `query?`, `limit?` (default: `20`)
    - **Usage**: Searches chat history filtered by specific media type or keyword.

46. `telegram_send_saved_message`
    - **Arguments**: `text?`, `file_path?`
    - **Usage**: Sends a note or document directly to Telegram "Saved Messages" (`InputPeerSelf`).

47. `telegram_get_saved_messages`
    - **Arguments**: `limit?` (default: `20`)
    - **Usage**: Retrieves messages and files saved in Telegram "Saved Messages".

48. `telegram_download_profile_photo`
    - **Arguments**: `bot_username`, `output_dir?`
    - **Usage**: Downloads user, bot, channel, or group avatar for AI visual inspection.

49. `telegram_send_location`
    - **Arguments**: `bot_username`, `latitude`, `longitude`, `title?`, `address?`, `provider?`, `reply_to_msg_id?`, `topic_id?`
    - **Usage**: Sends geographic coordinates or a named venue location to a bot or chat.

50. `telegram_get_user_profile`
    - **Arguments**: `user_identifier`
    - **Usage**: Retrieves full profile metadata including biography, Telegram Premium status, verification badge, fake/scam flags, and mutual groups.

51. `telegram_get_participant_permissions`
    - **Arguments**: `chat_identifier`, `user_identifier`
    - **Usage**: Inspects granular admin rights or restriction rules for a specific member/bot in a group or channel.

52. `telegram_block_peer`
    - **Arguments**: `peer_identifier`
    - **Usage**: Blocks a user or bot from contacting you.

53. `telegram_unblock_peer`
    - **Arguments**: `peer_identifier`
    - **Usage**: Unblocks a previously blocked user or bot.

54. `telegram_get_blocked_peers`
    - **Arguments**: `limit?` (default: `50`)
    - **Usage**: Retrieves list of all currently blocked peers with privacy-masked phone numbers.

55. `telegram_get_dialog_filters`
    - **Arguments**: None
    - **Usage**: Retrieves configured Telegram chat folders/filters (e.g. Work, Bots, Channels) with folder IDs, titles, and rule counts.

56. `telegram_create_chat`
    - **Arguments**: `title`, `about?`, `megagroup?` (default: `True`), `for_forum?` (default: `False`)
    - **Usage**: Creates a new supergroup, channel, or forum supergroup for isolated testing workflows.

57. `telegram_delete_chat`
    - **Arguments**: `chat_identifier`
    - **Usage**: Permanently deletes a channel or supergroup created by the account.

58. `telegram_create_invite_link`
    - **Arguments**: `chat_identifier`, `title?`, `expire_in_seconds?`, `expire_date_iso?`, `usage_limit?`, `request_needed?` (default: `False`)
    - **Usage**: Generates customizable chat invite links with expiration timestamps, member limits, and approval gates.

59. `telegram_create_dialog_filter`
    - **Arguments**: `title`, `emoticon?`, `filter_id?`, `contacts?`, `non_contacts?`, `groups?`, `broadcasts?`, `bots?`, `exclude_muted?`, `exclude_read?`, `exclude_archived?`
    - **Usage**: Creates a new Telegram chat folder/filter to categorize chats (e.g., Bots, Work, Crypto).

60. `telegram_delete_dialog_filter`
    - **Arguments**: `filter_id`
    - **Usage**: Deletes a Telegram chat folder/filter by folder ID.
