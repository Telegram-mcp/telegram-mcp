# 📋 Changelog

All notable changes to **`telegram-mcp`** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html), and includes timestamps in `Asia/Kolkata` (IST).

---

## [v1.11.0] — 2026-09-05 (21:20 IST)
`[2026-09-05]{21:20:00} v1.11.0 Release: Added member permissions inspection and peer blocking management #54 total MCP tools`

### 🚀 New Features
* **Granular Member & Admin Permissions Inspector (`telegram_get_participant_permissions`)**: Inspects granular admin rights (`change_info`, `post_messages`, `edit_messages`, `delete_messages`, `ban_users`, `invite_users`, `pin_messages`, `add_admins`, `manage_topics`) and restriction rules (`send_messages`, `send_media`, `send_stickers`, `embed_links`, `send_polls`, `until_date`) for any member or bot in channels and supergroups.
* **Peer Blocking & Blocklist Management (`telegram_block_peer`, `telegram_unblock_peer`, `telegram_get_blocked_peers`)**: Allows automated agents to block or unblock users and bots, and retrieve the full active blocklist with masked phone numbers.

---

## [v1.10.0] — 2026-09-05 (21:16 IST)
`[2026-09-05]{21:16:00} v1.10.0 Release: Added geolocation & venue dispatch and extended user profile & premium inspector #50 total MCP tools`

### 🚀 New Features
* **Location & Venue Dispatch (`telegram_send_location`)**: Allows automated agents to send precise coordinates (`latitude`, `longitude`) or named venues (`title`, `address`, `provider`) with forum topic support for testing delivery, taxi, weather, and map bots.
* **Extended User & Bot Profile Inspector (`telegram_get_user_profile`)**: Retrieves complete user profile metadata including biography/about text, Telegram Premium status, verification badge, fake/scam warnings, and mutual groups count with automatic phone privacy masking.

---

## [v1.9.0] — 2026-09-05 (20:58 IST)
`[2026-09-05]{20:58:00} v1.9.0 Release: Added poll voting, vote retraction, media search, saved messages, avatar download, rate limit telemetry, and forum topic support #48 total MCP tools`

### 🚀 New Features
* **Poll Voting & Revocation (`telegram_vote_poll`, `telegram_retract_vote`)**: Allows automated agents to cast votes on single-choice or multi-choice native Telegram polls/quizzes and revoke previously submitted votes.
* **Filtered Media Search (`telegram_search_media`)**: Searches chat history filtered by specific media type (`photo`, `document`, `video`, `voice`, `audio`, `gif`, `url`) with optional keyword queries.
* **Telegram Saved Messages (`telegram_send_saved_message`, `telegram_get_saved_messages`)**: Direct reading and writing into the user's personal Telegram "Saved Messages" cloud storage (`InputPeerSelf`).
* **Profile Photo & Avatar Retrieval (`telegram_download_profile_photo`)**: Downloads profile pictures and avatars of users, bots, channels, and groups for AI visual analysis.
* **Supergroup Forum Topics Support**: Added `topic_id` parameter to `send_message`, `send_file`, and `send_album` to target specific forum thread topics within Telegram supergroups.
* **Authorless Message Forwarding**: Added `drop_author` flag to `telegram_forward_messages` for clean reposts without original forward headers.
* **Flood & Rate Limit Telemetry**: Configured `flood_sleep_threshold` on Telethon client to eliminate silent 60s freeze hangs and exposed real-time rate limit event telemetry in `telegram_status`.

---

## [v1.8.0] — 2026-09-05 (20:43 IST)
`[2026-09-05]{20:43:00} v1.8.0 Release: Added Mini App WebApp URL extraction, persistent reply keyboard clicking, chat actions, group join/leave, and HTTP URL file dispatch #42 total MCP tools`

### 🚀 New Features
* **Telegram Mini App Testing (`telegram_get_web_app_url`)**: Extracts authenticated Web App launch URLs from Mini App buttons for frontend testing via Playwright / browser tools.
* **Persistent Reply Keyboard Clicking (`telegram_click_reply_button`)**: Clicks buttons in bottom-screen persistent menus (`ReplyKeyboardMarkup`) and dispatches selections.
* **Presence & Chat Actions (`telegram_send_chat_action`)**: Broadcasts typing and upload indicators (`typing`, `upload_photo`, `record_video`, `upload_document`, etc.).
* **Channel & Group Management (`telegram_join_chat`, `telegram_leave_chat`)**: Joins public channels or private chats via invite links, and cleanly leaves chats.
* **Direct Web URL Media Dispatch**: `telegram_send_file` and `telegram_send_album` now directly stream external HTTP/HTTPS URLs without requiring local file saving.

---

## [v1.7.0] — 2026-09-05 (20:39 IST)
`[2026-09-05]{20:39:00} CI & Testing Infrastructure: Added GitHub Actions multi-version CI, unit test suite with mocks, secret leak detection, and Dependabot #CI pipeline`

### 🚀 CI & Quality Assurance
* **Automated GitHub Actions CI (`.github/workflows/ci.yml`)**: Automated pipeline testing across Python 3.10, 3.11, and 3.12.
* **Mock Unit Test Suite (`tests/`)**: 100% offline unit tests for `TelegramService` and `server.py` verifying tool registration, message formatting, URL cleaning, and phone privacy masking.
* **Credential Leak Guard**: Added CI check to prevent committing `.env` or sensitive credentials into git.
* **Dependabot Configuration (`.github/dependabot.yml`)**: Automated weekly dependency security monitoring.
* **Dev Dependencies (`requirements-dev.txt`)**: Clean separation of test and development tooling.

---

## [v1.6.0] — 2026-09-05 (20:32 IST)
`[2026-09-05]{20:32:00} v1.6.0 Release: Added drafts, scheduled messages, pinned filters, mute/unmute, chat export transcripts, member directory, contacts, peer resolver, and standalone wait_for #37 total MCP tools`

### 🚀 New Features
* **Explicit Wait Engine (`telegram_wait_for`)**: Dedicated tool to wait for asynchronous bot responses, substring containment, message edits, or progress updates without manual agent polling.
* **Draft Management (`telegram_save_draft`)**: Saves uncommitted message drafts into chat input boxes with optional reply-to target.
* **Scheduled Messaging (`telegram_schedule_message`, `telegram_get_scheduled_messages`, `telegram_delete_scheduled_messages`)**: Schedule messages for future automated delivery, view scheduled queue, and cancel scheduled deliveries.
* **Pinned Message Direct Filter (`telegram_get_pinned_messages`)**: Retrieve pinned messages directly from chats, bots, or channels.
* **Mute & Unmute Chat Notifications (`telegram_mute_chat`, `telegram_unmute_chat`)**: Control notification muting for specified time intervals or permanently.
* **LLM Chat Export & Transcripts (`telegram_export_chat`)**: Export full conversation history formatted as clean Markdown or structured JSON for agent digest and summarization.
* **Participant Inspection (`telegram_get_chat_members`)**: List group and channel participants with names, usernames, and bot badges.
* **Contacts Directory (`telegram_get_contacts`)**: Retrieve and filter saved contacts with automatic phone masking.
* **Entity Resolver (`telegram_resolve_peer`)**: Resolves usernames, phone numbers, or IDs to complete entity metadata.

---

## [v1.5.0] — 2026-09-05 (20:20 IST)

### 🚀 New Features
* **Bot Inspection (`telegram_get_bot_info`)**: Fetches full bot profile info including about text, description, and registered command definitions.
* **Message Pinning & Unpinning (`telegram_pin_message`, `telegram_unpin_message`)**: Pin announcements or test status messages, and unpin individually or in bulk.
* **Message Context Fetching (`telegram_get_message_context`)**: Fetches surrounding dialogue context around a specific message ID for test diagnosis.
* **Grouped Albums (`telegram_send_album`)**: Sends multiple photos/documents grouped together as an album in a single message.

---

## [v1.4.0] — 2026-09-05 (20:15 IST)

### 🚀 New Features
* **Message Editing & Deletion**: Added `telegram_edit_message` and `telegram_delete_messages` for automated message mutation and teardown.
* **Message Forwarding**: Added `telegram_forward_messages` to test bots handling forwarded media and verification proofs.
* **Emoji Reactions**: Added `telegram_send_reaction` to send or clear emoji reactions on messages (`👍`, `🔥`, `❤️`, etc.).
* **Poll & Quiz Dispatch**: Added `telegram_send_poll` to generate and send native Telegram polls and quizzes.
* **Dialog & Chat Management**: Added `telegram_list_dialogs` to list recent chats and unread counts, and `telegram_mark_chat_read` to acknowledge messages.
* **Chat Search**: Added `telegram_search_messages` to search message history by keyword.
* **Formatting & Voice Notes**: Added `parse_mode` (`"md"`/`"html"`) support in `telegram_send_message` and `voice_note` flag in `telegram_send_file`.
* **Privacy Protection**: Phone numbers in `telegram_status` are now masked automatically.

---

## [v1.3.0] — 2026-09-05 (17:45 IST)

### 🛡️ Session Protection
* **Process-level file lock (`fcntl`)**: Prevents multiple `server.py` instances from connecting with the same Telegram session simultaneously, which previously caused Telegram to permanently revoke the auth key (`AuthKeyDuplicatedError`).
* **Clear error on dead sessions**: Detects `AuthKeyDuplicatedError` and returns an actionable message explaining the session is permanently revoked and how to re-login, instead of a cryptic Telethon traceback.

### 🔄 Connection Resilience
* **Auto-reconnect on transient errors**: Added `_ensure_connected()` wrapper that retries once on `ConnectionError`/`OSError` before giving up, handling temporary network drops gracefully.
* **Non-crashing server startup**: The server starts up gracefully even when unauthenticated or when the session is invalid, ensuring MCP controls (restart/disable) remain responsive in UI clients.
* **Proper lifecycle management**: Added MCPServer `lifespan` context manager that cleanly disconnects the Telethon client on shutdown.
* **Graceful shutdown**: Added `disconnect()` method and signal handlers (`SIGTERM`/`SIGINT`) ensuring the Telegram connection and process lock are always released cleanly.

### 🔑 Diagnostics
* **Diagnostics Tool (`telegram_status`)**: Inspect connection state, auth validity, and configuration without crashing.

---

## [v1.2.0] — 2026-08-30 (15:40 IST)

### 🚀 New Features
* **Live Python Code Execution Sandbox (`telegram_execute_code`)**: Added direct async execution tool allowing AI agents to run custom Telethon and MTProto scripts on the authenticated client.
* **Multi-Step Test Suite Runner (`telegram_run_test_suite`)**: Executes complete end-to-end regression workflows with assertions and configurable `sleep` intervals.
* **Media & Document Verification**: Added `telegram_send_file` (upload photos, docs, audio) and `telegram_download_media` (inspect bot-generated media locally).
* **Inline Query Mode (`telegram_inline_query`)**: Added simulation and result parsing for `@bot query` inline modes.

### 🛡️ Security & Environment
* **Environment Alignment Rule**: Enforced strict DC 2 Sandbox isolation for test accounts and production isolation for live accounts.
* **Secret Sanitization**: Verified automated scans for `.env` exclusion and secret leak prevention.

### 🧹 Refactoring & Cleanup
* **Pure Python Migration**: Complete transition to Python 3 + Telethon + official MCP SDK (`MCPServer`).
* **Housekeeping**: Removed deprecated TypeScript build artifacts (`src/`, `package.json`, `tsconfig.json`).
* **Documentation**: Added dedicated [`docs/AGENT_GUIDE.md`](docs/AGENT_GUIDE.md) and modernized [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## [v1.0.0] — 2026-08-30 (14:04 IST)

### 🚀 Initial Release
* First release of the Telegram Bot Testing MCP Server.
* Supported command dispatch (`/start`, `/help`), message sending, and inline keyboard button clicking via MTProto.
* Integrated workspace discovery for Antigravity (`agy` CLI).
