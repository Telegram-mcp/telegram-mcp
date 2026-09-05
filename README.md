# Telegram MCP 🤖🧪

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Telegram-mcp/telegram-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Telegram-mcp/telegram-mcp/actions/workflows/ci.yml)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple.svg)](https://modelcontextprotocol.io)
[![Telethon](https://img.shields.io/badge/Telethon-MTProto-blue.svg)](https://github.com/LonamiWebs/Telethon)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> [!WARNING]
> **Disclaimer**: This project is an independent open-source tool and is **not affiliated with, authorized, maintained, sponsored, or endorsed by Telegram FZ-LLC, Telegram Messenger Inc., or any of their affiliates**. "Telegram" is a registered trademark of its respective owners.

A Model Context Protocol (**MCP**) server that allows AI Coding Agents (such as Antigravity, Claude Desktop, Cursor, and custom agent backends) to autonomously **interact with, test, click buttons on, and verify Telegram bots** end-to-end.

> 📖 **AI Agents**: See the dedicated [**AI Agent Testing Guide**](docs/AGENT_GUIDE.md) for tool selection workflows, test suites, and best practices.

> [!TIP]
> **Environment Recommendation**: We strongly recommend using the **Test Server** (`TELEGRAM_TEST_MODE=true`) for bot development and automated testing because it carries **zero risk to your main personal Telegram account**.
> *Note: Make sure your target bot and user account are on the **same environment** (Test Server bot ↔ Test Server account, or Prod bot ↔ Prod account), as Telegram test and production networks are completely isolated.*

---

## 🌟 Features

* **Command & Message Dispatch**: Send commands (`/start`, `/help`, `/settings`) and text payloads to any target bot.
* **Inline Keyboard Navigation**: Click inline callback buttons (`CallbackQuery`), trigger button menus, and inspect in-place message updates.
* **Multi-Step Test Suite Runner (`telegram_run_test_suite`)**: Execute full regression test scenarios with assertions and `sleep` delays in a single tool call.
* **Media & File Testing**: Send photos, documents, audio, or PDFs to bots, and download returned media to verify generated files.
* **Inline Query Mode**: Test `@bot query` inline modes and inspect returned inline articles and preview metadata.
* **Python Code Execution Sandbox (`telegram_execute_code`)**: Run custom asynchronous Python scripts with direct access to the live `TelegramClient` and raw MTProto functions.
* **Clean State Management**: Clear dialog history before/after test runs for idempotent testing.

---

## 🚀 Quickstart

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/Telegram-mcp/telegram-mcp.git
cd telegram-mcp
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Add your Telegram API credentials from [my.telegram.org](https://my.telegram.org):
```ini
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_TEST_MODE=false
```

### 3. Generate Session (One-Time Login)

Run the interactive login script:
```bash
python3 login.py
```
* Enter your phone number and the verification code sent to your Telegram app.
* The script saves your `TELEGRAM_SESSION` string automatically into `.env`.

### 4. Run the MCP Server

```bash
python3 server.py
```

---

## 🔌 Connecting to AI Agents

### Antigravity CLI (`agy`) / Gemini
The repository includes a pre-configured `.agents/plugins/telegram-bot/` plugin. Any `agy` session started in this workspace will automatically discover and load the tools.

### Claude Desktop
Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "telegram-bot": {
      "command": "python3",
      "args": ["/path/to/telegram-bot-mcp/server.py"],
      "env": {
        "TELEGRAM_API_ID": "your_api_id",
        "TELEGRAM_API_HASH": "your_api_hash",
        "TELEGRAM_SESSION": "your_session_string",
        "TELEGRAM_TEST_MODE": "false"
      }
    }
  }
}
```

---

## 🛠️ MCP Tools Reference

| Tool Name | Parameters | Purpose |
| :--- | :--- | :--- |
| `telegram_status` | _None_ | Checks connection health, environment, and user info with masked phone for privacy. |
| `telegram_send_command` | `bot_username`, `command`, `wait_response?`, `timeout_seconds?` | Sends a command and waits for reply. |
| `telegram_send_message` | `bot_username`, `text`, `reply_to_msg_id?`, `parse_mode?`, `wait_response?` | Sends text payloads or queries with Markdown/HTML formatting. |
| `telegram_edit_message` | `bot_username`, `message_id`, `new_text`, `parse_mode?` | Edits a previously sent message by ID. |
| `telegram_delete_messages` | `bot_username`, `message_ids`, `revoke?` | Deletes messages by ID for clean teardown. |
| `telegram_forward_messages` | `to_chat`, `from_chat`, `message_ids` | Forwards messages from one chat/bot to another. |
| `telegram_send_reaction` | `bot_username`, `message_id`, `reaction` | Sends an emoji reaction (👍, 🔥, ❤️, etc.) to a message. |
| `telegram_send_poll` | `bot_username`, `question`, `options`, `is_quiz?`, `correct_option_id?` | Sends native polls or quizzes. |
| `telegram_mark_chat_read` | `bot_username`, `max_id?` | Marks dialog history as read. |
| `telegram_list_dialogs` | `limit?` | Lists recent chats, groups, bots, and channels with unread counts. |
| `telegram_search_messages` | `bot_username`, `query`, `limit?` | Searches message history by text query keyword. |
| `telegram_click_inline_button` | `bot_username`, `message_id?`, `button_text?`, `button_index?` | Clicks inline buttons and returns updated message state. |
| `telegram_send_file` | `bot_username`, `file_path`, `caption?`, `voice_note?` | Uploads images/documents/audio (or circular voice notes). |
| `telegram_download_media` | `bot_username`, `message_id`, `output_dir?` | Downloads media from bot messages. |
| `telegram_inline_query` | `bot_username`, `query` | Performs inline queries (`@bot query`). |
| `telegram_send_and_verify` | `bot_username`, `input_text`, `expected_contains` | Convenience single-step assertion. |
| `telegram_run_test_suite` | `bot_username`, `steps` | Runs multi-step test workflows with `sleep` and assertions. |
| `telegram_get_bot_info` | `bot_username` | Inspects a bot's description, about text, commands list, and profile metadata. |
| `telegram_pin_message` | `bot_username`, `message_id`, `notify?` | Pins a message in the chat with the bot or group. |
| `telegram_unpin_message` | `bot_username`, `message_id?` | Unpins a specific message, or unpins all messages in the chat. |
| `telegram_get_message_context` | `bot_username`, `message_id`, `limit_before?`, `limit_after?` | Fetches preceding and succeeding messages around a message ID. |
| `telegram_send_album` | `bot_username`, `file_paths`, `caption?` | Sends multiple photos/files as a grouped album in one message. |
| `telegram_save_draft` | `bot_username`, `text`, `reply_to_msg_id?` | Saves an uncommitted draft directly into the Telegram chat input box. |
| `telegram_schedule_message` | `bot_username`, `text`, `schedule_in_seconds?`, `schedule_date_iso?` | Schedules a message for future automated delivery. |
| `telegram_get_scheduled_messages` | `bot_username` | Retrieves all pending scheduled messages queued in a chat. |
| `telegram_delete_scheduled_messages` | `bot_username`, `message_ids` | Cancels and deletes scheduled messages before delivery. |
| `telegram_get_pinned_messages` | `bot_username`, `limit?` | Fetches pinned messages directly from a chat, bot, or channel. |
| `telegram_mute_chat` | `bot_username`, `duration_seconds?` | Mutes notifications for a specified duration or permanently. |
| `telegram_unmute_chat` | `bot_username` | Unmutes notifications for a chat or channel. |
| `telegram_export_chat` | `bot_username`, `limit?`, `format?` | Exports conversation history as clean Markdown or JSON for AI summarization. |
| `telegram_get_chat_members` | `bot_username`, `limit?` | Lists group/channel participants with names, IDs, and bot flags. |
| `telegram_get_contacts` | `query?`, `limit?` | Retrieves saved Telegram contacts with privacy-masked phone numbers. |
| `telegram_resolve_peer` | `peer` | Resolves any username, phone, or ID to detailed entity metadata and type. |
| `telegram_wait_for` | `bot_username`, `text_contains?`, `after_message_id?`, `target_message_id?`, `wait_for_edit?`, `timeout_seconds?` | Waits for an incoming message, specific substring, or message edit/progress update. |
| `telegram_get_web_app_url` | `bot_username`, `message_id?`, `button_text?`, `button_index?` | Extracts authenticated Web App launch URLs from Telegram Mini App buttons for frontend testing. |
| `telegram_click_reply_button` | `bot_username`, `button_text?`, `button_index?`, `wait_response?` | Clicks buttons in persistent bottom reply keyboards and dispatches user actions. |
| `telegram_send_chat_action` | `bot_username`, `action?` | Broadcasts chat presence indicators ('typing', 'upload_photo', 'record_video', etc.). |
| `telegram_join_chat` | `chat_identifier` | Joins a public channel/supergroup via @username or private chat via invite link (t.me/+...). |
| `telegram_leave_chat` | `chat_identifier` | Leaves a channel or group by username or ID. |
| `telegram_vote_poll` | `bot_username`, `message_id`, `option_index` | Casts a vote on a specific option in a poll or quiz message. |
| `telegram_retract_vote` | `bot_username`, `message_id` | Retracts a previously submitted poll vote. |
| `telegram_search_media` | `bot_username`, `media_type?`, `query?`, `limit?` | Searches chat messages filtered by media type ('photo', 'document', 'url', 'video', etc.). |
| `telegram_send_saved_message` | `text`, `file_path?` | Sends a message or file to your personal Telegram 'Saved Messages' cloud chat (InputPeerSelf). |
| `telegram_get_saved_messages` | `limit?` | Retrieves recent messages from your personal Telegram 'Saved Messages' cloud chat. |
| `telegram_download_profile_photo` | `bot_username`, `output_dir?` | Downloads the profile photo or avatar of any user, bot, or group for visual inspection. |
| `telegram_send_location` | `bot_username`, `latitude`, `longitude`, `title?`, `address?`, `provider?` | Sends geographic coordinates or a named venue to a bot or chat. |
| `telegram_get_user_profile` | `user_identifier` | Retrieves full profile metadata (about, Telegram Premium, verified, badges). |
| `telegram_get_participant_permissions` | `chat_identifier`, `user_identifier` | Inspects administrator or restricted permissions of a user or bot in a group/channel. |
| `telegram_block_peer` | `peer_identifier` | Blocks a user or bot from contacting you. |
| `telegram_unblock_peer` | `peer_identifier` | Unblocks a previously blocked user or bot. |
| `telegram_get_blocked_peers` | `limit?` | Retrieves the list of currently blocked users and bots. |
| `telegram_execute_code` | `code`, `timeout_seconds?` | Executes arbitrary Python code with live Telethon client access. |
| `telegram_get_chat_history` | `bot_username`, `limit?` | Fetches recent conversation history. |
| `telegram_clear_chat` | `bot_username` | Clears conversation dialog for clean tests. |

---

## 🧪 Example Test Suite Scenario

```json
[
  {"action": "send", "text": "/start"},
  {"action": "sleep", "seconds": 1.0},
  {"action": "assert_reply", "contains": "Welcome to my bot!"},
  {"action": "click_button", "text": "Settings"},
  {"action": "sleep", "seconds": 0.5},
  {"action": "assert_reply", "contains": "Notification Preferences"}
]
```

---

## 🔬 Running Unit Tests

Run the test suite locally with `pytest` or Python's built-in `unittest`:

```bash
pip install -r requirements-dev.txt
python3 -m pytest tests -v
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

