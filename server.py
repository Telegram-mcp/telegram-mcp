#!/usr/bin/env python3
import json
import signal
import sys
import asyncio
from typing import Optional, List, Dict, Any, Union
from contextlib import asynccontextmanager

from mcp.server.mcpserver import MCPServer
from telethon import errors
from telegram_service import telegram_service


@asynccontextmanager
async def lifespan(server):
    try:
        await telegram_service.get_client()
    except Exception as e:
        print(f"[telegram-mcp] Startup warning: {e}", file=sys.stderr)
        print("[telegram-mcp] Server is running but Telegram is not connected.", file=sys.stderr)
        print("[telegram-mcp] Use the telegram_status tool to check or run: python3 /root/bot-mcp/login.py", file=sys.stderr)
    try:
        yield {}
    finally:
        await telegram_service.disconnect()


MCP_INSTRUCTIONS = """Telegram MCP Server (Telethon + MTProto).

If tools return auth errors, the session needs to be regenerated:
1. Run: cd /root/bot-mcp && python3 login.py
2. Restart the MCP server.

Use telegram_status to check the current connection state before running other tools."""

mcp = MCPServer("telegram-mcp", instructions=MCP_INSTRUCTIONS, lifespan=lifespan)


@mcp.tool()
async def telegram_status() -> str:
    """
    Checks the current Telegram connection state, session validity, and environment configuration.
    Call this first to diagnose auth issues before using other tools.
    """
    import os
    status = {
        "test_mode": os.environ.get("TELEGRAM_TEST_MODE", "false"),
        "api_id_set": bool(os.environ.get("TELEGRAM_API_ID")),
        "api_hash_set": bool(os.environ.get("TELEGRAM_API_HASH")),
        "session_set": bool(os.environ.get("TELEGRAM_SESSION")),
        "default_bot": os.environ.get("DEFAULT_TARGET_BOT", "(not set)"),
        "rate_limiting": {
            "flood_wait_events": getattr(telegram_service, "flood_wait_events", 0),
            "last_flood_wait_seconds": getattr(telegram_service, "last_flood_wait_seconds", 0),
        },
        "proxy": {
            "configured": bool(os.environ.get("TELEGRAM_PROXY_HOST")),
            "type": os.environ.get("TELEGRAM_PROXY_TYPE", "socks5").lower() if os.environ.get("TELEGRAM_PROXY_HOST") else None,
            "host": os.environ.get("TELEGRAM_PROXY_HOST"),
            "port": int(os.environ.get("TELEGRAM_PROXY_PORT", "1080")) if os.environ.get("TELEGRAM_PROXY_HOST") else None,
        },
    }

    if not status["session_set"]:
        status["connected"] = False
        status["error"] = "No TELEGRAM_SESSION in .env. Run: cd /root/bot-mcp && python3 login.py"
        return json.dumps(status, indent=2)

    try:
        client = await telegram_service.get_client()
        me = await client.get_me()
        status["connected"] = True
        phone_masked = None
        if me.phone:
            p = str(me.phone)
            phone_masked = f"+{p[:2]} {'*' * (len(p) - 6)} {p[-4:]}" if len(p) > 6 else ("*" * len(p))

        status["user"] = {
            "id": me.id,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "username": me.username,
            "phone": phone_masked,
        }
    except Exception as e:
        status["connected"] = False
        err = str(e)
        if "AuthKeyDuplicated" in err or "authorization key" in err.lower():
            status["error"] = "Session permanently revoked (AuthKeyDuplicatedError). Run: cd /root/bot-mcp && python3 login.py"
        elif "not authorized" in err.lower():
            status["error"] = "Session expired or invalid. Run: cd /root/bot-mcp && python3 login.py"
        else:
            status["error"] = err

    return json.dumps(status, indent=2)


@mcp.tool()
async def telegram_execute_code(
    code: str,
    timeout_seconds: int = 30,
) -> str:
    """
    Executes arbitrary custom asynchronous Python code with direct access to the live Telethon client and MTProto API.
    Available pre-injected variables:
      - `client`: Authenticated Telethon TelegramClient instance (e.g. `await client.get_dialogs()`, `await client(...)`)
      - `service` / `telegram_service`: The TelegramService instance
      - `events`: telethon.events
      - `functions`: telethon.tl.functions (raw MTProto functions)
      - `types`: telethon.tl.types (raw MTProto types)
      - `asyncio`, `json`, `os`, `time`
    Stdout/stderr and return values are captured and returned in the JSON result.
    """
    try:
        res = await telegram_service.execute_code(code, timeout_seconds=timeout_seconds)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_command(
    bot_username: str,
    command: str,
    wait_response: bool = True,
    timeout_seconds: int = 10,
) -> str:
    """
    Sends a bot command (e.g. /start, /help, /settings) to the target bot and optionally waits for response.
    """
    try:
        sent = await telegram_service.send_message(bot_username, command)
        response = None
        if wait_response:
            response = await telegram_service.wait_for_reply(
                bot_username,
                after_message_id=sent["id"],
                timeout_seconds=timeout_seconds,
            )

        return json.dumps(
            {
                "status": "success",
                "sent_command": sent,
                "bot_response": response or ("Timeout waiting for response" if wait_response else None),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_message(
    bot_username: str,
    text: str,
    reply_to_msg_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    parse_mode: Optional[str] = "md",
    wait_response: bool = True,
    timeout_seconds: int = 10,
) -> str:
    """
    Sends a text message or payload to the target bot or chat. Supports Markdown ('md') or HTML ('html') formatting.
    Use topic_id to route directly into a supergroup forum topic.
    """
    try:
        sent = await telegram_service.send_message(
            bot_username=bot_username,
            text=text,
            reply_to_msg_id=reply_to_msg_id,
            topic_id=topic_id,
            parse_mode=parse_mode,
        )
        response = None
        if wait_response:
            response = await telegram_service.wait_for_reply(
                bot_username,
                after_message_id=sent["id"],
                timeout_seconds=timeout_seconds,
            )

        return json.dumps(
            {
                "status": "success",
                "sent_message": sent,
                "bot_response": response or ("Timeout waiting for response" if wait_response else None),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_file(
    bot_username: str,
    file_path: str,
    caption: Optional[str] = None,
    reply_to_msg_id: Optional[int] = None,
    topic_id: Optional[int] = None,
    voice_note: bool = False,
    wait_response: bool = True,
    timeout_seconds: int = 15,
) -> str:
    """
    Sends a file, photo, document, voice note, or media to the bot and optionally waits for its response.
    Use topic_id to post into supergroup forum topics.
    Set voice_note=True to send audio as a circular/native Telegram voice message.
    """
    try:
        sent = await telegram_service.send_file(
            bot_username=bot_username,
            file_path=file_path,
            caption=caption,
            reply_to_msg_id=reply_to_msg_id,
            topic_id=topic_id,
            voice_note=voice_note,
        )
        response = None
        if wait_response:
            response = await telegram_service.wait_for_reply(
                bot_username,
                after_message_id=sent["id"],
                timeout_seconds=timeout_seconds,
            )

        return json.dumps(
            {
                "status": "success",
                "sent_file": sent,
                "bot_response": response or ("Timeout waiting for response" if wait_response else None),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_download_media(
    bot_username: str,
    message_id: int,
    output_dir: Optional[str] = None,
) -> str:
    """
    Downloads media (photo, document, audio, chart) attached to a bot's message to inspect or verify its content.
    """
    try:
        res = await telegram_service.download_media(
            bot_username=bot_username,
            message_id=message_id,
            output_dir=output_dir,
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_click_inline_button(
    bot_username: str,
    message_id: Optional[int] = None,
    button_text: Optional[str] = None,
    button_index: Optional[int] = None,
    wait_update: bool = True,
) -> str:
    """
    Clicks an inline keyboard button on a specific bot message (or latest message if omitted).
    """
    try:
        res = await telegram_service.click_inline_button(
            bot_username=bot_username,
            message_id=message_id,
            button_text=button_text,
            button_index=button_index,
            wait_update=wait_update,
        )
        return json.dumps(
            {
                "status": "success",
                "action": "clicked_button",
                "message_id": res.get("message_id"),
                "popup_alert": res.get("popup_alert"),
                "updated_message": res.get("updated_message"),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_inline_query(
    bot_username: str,
    query: str,
) -> str:
    """
    Performs an inline query against the bot (e.g. '@my_bot search') and retrieves the list of returned inline results.
    """
    try:
        results = await telegram_service.inline_query(bot_username, query)
        return json.dumps(
            {
                "status": "success",
                "query": query,
                "count": len(results),
                "results": results,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_and_verify(
    bot_username: str,
    input_text: str,
    expected_contains: str,
    timeout_seconds: int = 10,
) -> str:
    """
    Sends text or command to the bot and asserts that the bot's reply contains expected text.
    """
    try:
        sent = await telegram_service.send_message(bot_username, input_text)
        reply = await telegram_service.wait_for_reply(
            bot_username,
            after_message_id=sent["id"],
            timeout_seconds=timeout_seconds,
        )

        if not reply:
            return json.dumps(
                {
                    "verified": False,
                    "reason": "Timeout waiting for bot response",
                    "sent": sent,
                },
                indent=2,
            )

        passed = expected_contains.lower() in reply.get("text", "").lower()

        return json.dumps(
            {
                "verified": passed,
                "expected": expected_contains,
                "received_text": reply.get("text", ""),
                "available_buttons": reply.get("buttons") or [],
                "message_id": reply.get("id"),
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_run_test_suite(
    bot_username: str,
    steps: List[Dict[str, Any]],
) -> str:
    """
    Executes a multi-step test scenario against a bot with sleep/wait support in a single call.
    Supported actions in steps:
      - {"action": "send", "text": "/start"}
      - {"action": "send_file", "file_path": "/path/to/test.png", "caption": "Optional"}
      - {"action": "sleep", "seconds": 2.5}
      - {"action": "assert_reply", "contains": "Welcome", "timeout_seconds": 10}
      - {"action": "click_button", "text": "Settings", "message_id": 1234}
      - {"action": "clear_chat"}
    """
    try:
        report = await telegram_service.run_test_suite(bot_username, steps)
        return json.dumps(report, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_chat_history(
    bot_username: str,
    limit: int = 10,
) -> str:
    """
    Fetches recent message history, media details, and inline keyboard buttons from the chat with the bot.
    """
    try:
        history = await telegram_service.get_chat_history(bot_username, limit=limit)
        return json.dumps(
            {
                "status": "success",
                "count": len(history),
                "messages": history,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_clear_chat(
    bot_username: str,
) -> str:
    """
    Clears the chat dialog history with the target bot for clean testing states.
    """
    try:
        await telegram_service.clear_chat(bot_username)
        return json.dumps(
            {
                "status": "success",
                "message": f"Chat dialog with {bot_username} cleared successfully.",
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_edit_message(
    bot_username: str,
    message_id: int,
    new_text: str,
    parse_mode: Optional[str] = "md",
) -> str:
    """
    Edits a previously sent message by ID. Useful for testing bot interactions that monitor message edits.
    """
    try:
        res = await telegram_service.edit_message(
            bot_username=bot_username,
            message_id=message_id,
            new_text=new_text,
            parse_mode=parse_mode,
        )
        return json.dumps({"status": "success", "edited_message": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_delete_messages(
    bot_username: str,
    message_ids: List[int],
    revoke: bool = True,
) -> str:
    """
    Deletes one or more messages by ID. Set revoke=True to delete for all participants.
    """
    try:
        res = await telegram_service.delete_messages(
            bot_username=bot_username,
            message_ids=message_ids,
            revoke=revoke,
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_forward_messages(
    to_chat: str,
    from_chat: str,
    message_ids: List[int],
    drop_author: bool = False,
) -> str:
    """
    Forwards messages from one chat to another.
    Set drop_author=True to send cleanly as a copy without the forwarded attribution header.
    """
    try:
        res = await telegram_service.forward_messages(
            to_chat=to_chat,
            from_chat=from_chat,
            message_ids=message_ids,
            drop_author=drop_author,
        )
        return json.dumps({"status": "success", "forwarded_count": len(res), "messages": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_reaction(
    bot_username: str,
    message_id: int,
    reaction: str,
) -> str:
    """
    Sends an emoji reaction (e.g. '👍', '🔥', '❤️', '🎉') to a specific message, or clears it if reaction is empty.
    """
    try:
        res = await telegram_service.send_reaction(
            bot_username=bot_username,
            message_id=message_id,
            reaction=reaction,
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_poll(
    bot_username: str,
    question: str,
    options: List[str],
    is_quiz: bool = False,
    correct_option_id: Optional[int] = None,
) -> str:
    """
    Creates and sends a native Telegram poll or quiz to the target bot or chat.
    """
    try:
        res = await telegram_service.send_poll(
            bot_username=bot_username,
            question=question,
            options=options,
            is_quiz=is_quiz,
            correct_option_id=correct_option_id,
        )
        return json.dumps({"status": "success", "sent_poll": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_mark_chat_read(
    bot_username: str,
    max_id: Optional[int] = None,
) -> str:
    """
    Marks messages in a chat or dialog as read up to max_id (or all messages if omitted).
    """
    try:
        res = await telegram_service.mark_chat_read(bot_username=bot_username, max_id=max_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_list_dialogs(
    limit: int = 20,
) -> str:
    """
    Lists recent dialogs, conversations, groups, and channels with their IDs, names, unread counts, and last messages.
    """
    try:
        dialogs = await telegram_service.list_dialogs(limit=limit)
        return json.dumps({"status": "success", "count": len(dialogs), "dialogs": dialogs}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_search_messages(
    bot_username: str,
    query: str,
    limit: int = 20,
) -> str:
    """
    Searches message history within a specific chat or bot by text query keyword.
    """
    try:
        msgs = await telegram_service.search_messages(bot_username=bot_username, query=query, limit=limit)
        return json.dumps({"status": "success", "query": query, "count": len(msgs), "messages": msgs}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_bot_info(
    bot_username: str,
) -> str:
    """
    Retrieves full bot profile information including title, description, about text, and registered commands.
    """
    try:
        info = await telegram_service.get_bot_info(bot_username)
        return json.dumps({"status": "success", "bot_info": info}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_pin_message(
    bot_username: str,
    message_id: int,
    notify: bool = False,
) -> str:
    """
    Pins a message in the chat with the bot or group.
    """
    try:
        res = await telegram_service.pin_message(bot_username, message_id, notify=notify)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_unpin_message(
    bot_username: str,
    message_id: Optional[int] = None,
) -> str:
    """
    Unpins a specific message, or unpins all messages in the chat if message_id is omitted.
    """
    try:
        res = await telegram_service.unpin_message(bot_username, message_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_message_context(
    bot_username: str,
    message_id: int,
    limit_before: int = 5,
    limit_after: int = 5,
) -> str:
    """
    Fetches the surrounding conversation context (preceding and succeeding messages) around a specific message ID.
    """
    try:
        res = await telegram_service.get_message_context(
            bot_username=bot_username,
            message_id=message_id,
            limit_before=limit_before,
            limit_after=limit_after,
        )
        return json.dumps({"status": "success", "context": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_album(
    bot_username: str,
    file_paths: List[str],
    caption: Optional[str] = None,
    reply_to_msg_id: Optional[int] = None,
    topic_id: Optional[int] = None,
) -> str:
    """
    Sends multiple photos or files grouped together as an album in a single message.
    Use topic_id to post into supergroup forum topics.
    """
    try:
        sent = await telegram_service.send_album(
            bot_username=bot_username,
            file_paths=file_paths,
            caption=caption,
            reply_to_msg_id=reply_to_msg_id,
            topic_id=topic_id,
        )
        return json.dumps({"status": "success", "album_count": len(sent), "items": sent}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_save_draft(
    bot_username: str,
    text: str,
    reply_to_msg_id: Optional[int] = None,
) -> str:
    """
    Saves an uncommitted message draft into the chat input field without sending it.
    The user will see this draft pre-filled in their Telegram client.
    """
    try:
        res = await telegram_service.save_draft(
            bot_username=bot_username,
            text=text,
            reply_to_msg_id=reply_to_msg_id,
        )
        return json.dumps({"status": "success", "draft": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_schedule_message(
    bot_username: str,
    text: str,
    schedule_in_seconds: Optional[int] = None,
    schedule_date_iso: Optional[str] = None,
) -> str:
    """
    Schedules a message to be automatically delivered at a future time.
    Provide either schedule_in_seconds (relative delay) or schedule_date_iso (ISO 8601 string).
    """
    try:
        res = await telegram_service.schedule_message(
            bot_username=bot_username,
            text=text,
            schedule_in_seconds=schedule_in_seconds,
            schedule_date_iso=schedule_date_iso,
        )
        return json.dumps({"status": "success", "scheduled_message": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_scheduled_messages(
    bot_username: str,
) -> str:
    """
    Retrieves all pending scheduled messages queued for delivery in the specified chat.
    """
    try:
        msgs = await telegram_service.get_scheduled_messages(bot_username=bot_username)
        return json.dumps({"status": "success", "count": len(msgs), "messages": msgs}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_delete_scheduled_messages(
    bot_username: str,
    message_ids: List[int],
) -> str:
    """
    Cancels or deletes one or more scheduled messages before they are delivered.
    """
    try:
        res = await telegram_service.delete_scheduled_messages(
            bot_username=bot_username,
            message_ids=message_ids,
        )
        return json.dumps({"status": "success", "result": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_pinned_messages(
    bot_username: str,
    limit: int = 10,
) -> str:
    """
    Retrieves pinned messages directly from a bot, group, or channel.
    """
    try:
        msgs = await telegram_service.get_pinned_messages(bot_username=bot_username, limit=limit)
        return json.dumps({"status": "success", "count": len(msgs), "messages": msgs}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_mute_chat(
    bot_username: str,
    duration_seconds: Optional[int] = None,
) -> str:
    """
    Mutes notifications for a chat, bot, or channel for a specified duration in seconds (or permanently if omitted).
    """
    try:
        res = await telegram_service.mute_chat(bot_username=bot_username, duration_seconds=duration_seconds)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_unmute_chat(
    bot_username: str,
) -> str:
    """
    Unmutes notifications for a chat, bot, or channel.
    """
    try:
        res = await telegram_service.unmute_chat(bot_username=bot_username)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_export_chat(
    bot_username: str,
    limit: int = 50,
    format: str = "markdown",
) -> str:
    """
    Exports conversation history formatted as clean Markdown or structured JSON, optimized for LLM processing.
    Format can be 'markdown' or 'json'.
    """
    try:
        res = await telegram_service.export_chat(bot_username=bot_username, limit=limit, format=format)
        return json.dumps({"status": "success", "export": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_chat_members(
    bot_username: str,
    limit: int = 50,
) -> str:
    """
    Lists participants of a group, chat, or channel with their names, IDs, and usernames.
    """
    try:
        members = await telegram_service.get_chat_members(bot_username=bot_username, limit=limit)
        return json.dumps({"status": "success", "count": len(members), "members": members}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_contacts(
    query: Optional[str] = None,
    limit: int = 50,
) -> str:
    """
    Retrieves the user's saved Telegram contacts, optionally filtering by name or username.
    Phone numbers are automatically masked for privacy.
    """
    try:
        contacts = await telegram_service.get_contacts(query=query, limit=limit)
        return json.dumps({"status": "success", "count": len(contacts), "contacts": contacts}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_resolve_peer(
    peer: str,
) -> str:
    """
    Resolves any Telegram entity identifier (username, phone, invite link, or ID) into detailed metadata
    (entity type, verified status, bot/channel/group flags).
    """
    try:
        info = await telegram_service.resolve_peer(peer=peer)
        return json.dumps({"status": "success", "entity": info}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_wait_for(
    bot_username: str,
    text_contains: Optional[str] = None,
    after_message_id: Optional[int] = None,
    target_message_id: Optional[int] = None,
    wait_for_edit: bool = False,
    timeout_seconds: int = 30,
    poll_interval: float = 1.0,
) -> str:
    """
    Waits for a bot reply, specific message text, or a message edit/progress update.
    Useful for asynchronous bot tasks, long-running processes, or verifying status changes.

    - bot_username: Target bot or chat username/ID.
    - text_contains: Optional substring that the incoming or edited message must contain.
    - after_message_id: Only consider new messages with an ID higher than this.
    - target_message_id: Wait for an edit/update on this specific message.
    - wait_for_edit: Set True to wait for an edit rather than a new message.
    - timeout_seconds: Maximum time to wait in seconds (default: 30).
    - poll_interval: Frequency in seconds to check for updates (default: 1.0).
    """
    try:
        res = await telegram_service.wait_for(
            bot_username=bot_username,
            text_contains=text_contains,
            after_message_id=after_message_id,
            target_message_id=target_message_id,
            wait_for_edit=wait_for_edit,
            timeout_seconds=timeout_seconds,
            poll_interval=poll_interval,
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_web_app_url(
    bot_username: str,
    message_id: Optional[int] = None,
    button_text: Optional[str] = None,
    button_index: Optional[int] = None,
) -> str:
    """
    Extracts the authenticated Web App launch URL from a Telegram Mini App button.
    The resulting URL can be passed to Playwright or a browser automation tool to test the frontend UI.
    """
    try:
        res = await telegram_service.get_web_app_url(
            bot_username=bot_username,
            message_id=message_id,
            button_text=button_text,
            button_index=button_index,
        )
        return json.dumps({"status": "success", "web_app": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_click_reply_button(
    bot_username: str,
    button_text: Optional[str] = None,
    button_index: Optional[int] = None,
    wait_response: bool = True,
    timeout_seconds: int = 15,
) -> str:
    """
    Clicks an active persistent reply keyboard button (bottom screen menu keyboard) by text or index.
    Dispatches the button selection and optionally waits for the bot's response.
    """
    try:
        res = await telegram_service.click_reply_button(
            bot_username=bot_username,
            button_text=button_text,
            button_index=button_index,
            wait_response=wait_response,
            timeout_seconds=timeout_seconds,
        )
        return json.dumps({"status": "success", "response": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_chat_action(
    bot_username: str,
    action: str = "typing",
) -> str:
    """
    Broadcasts a presence action indicator (e.g. 'typing', 'upload_photo', 'record_video', 'record_voice', 'choose_sticker', 'cancel').
    """
    try:
        res = await telegram_service.send_chat_action(bot_username=bot_username, action=action)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_join_chat(
    chat_identifier: str,
) -> str:
    """
    Joins a public channel/supergroup via @username or a private chat via invite link (t.me/+...).
    """
    try:
        res = await telegram_service.join_chat(chat_identifier=chat_identifier)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_leave_chat(
    chat_identifier: str,
) -> str:
    """
    Leaves a channel or supergroup by username or ID.
    """
    try:
        res = await telegram_service.leave_chat(chat_identifier=chat_identifier)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_vote_poll(
    bot_username: str,
    message_id: int,
    option_index: int,
) -> str:
    """
    Casts a vote on a specific option in a poll or quiz message.
    """
    try:
        res = await telegram_service.vote_poll(
            bot_username=bot_username,
            message_id=message_id,
            option_index=option_index,
        )
        return json.dumps({"status": "success", "vote": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_retract_vote(
    bot_username: str,
    message_id: int,
) -> str:
    """
    Retracts a previously submitted vote in a poll.
    """
    try:
        res = await telegram_service.retract_vote(
            bot_username=bot_username,
            message_id=message_id,
        )
        return json.dumps({"status": "success", "result": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_search_media(
    bot_username: str,
    media_type: str = "photo",
    query: str = "",
    limit: int = 20,
) -> str:
    """
    Searches and filters chat messages by media type.
    media_type options: 'photo', 'document', 'video', 'voice', 'audio', 'url', 'gif'.
    """
    try:
        msgs = await telegram_service.search_media(
            bot_username=bot_username,
            media_type=media_type,
            query=query,
            limit=limit,
        )
        return json.dumps({"status": "success", "media_type": media_type, "count": len(msgs), "messages": msgs}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_saved_message(
    text: str,
    file_path: Optional[str] = None,
) -> str:
    """
    Sends a message or file to your personal Telegram 'Saved Messages' cloud chat (InputPeerSelf).
    Ideal as a private cloud workspace or staging scratchpad for test logs and artifacts.
    """
    try:
        sent = await telegram_service.send_saved_message(text=text, file_path=file_path)
        return json.dumps({"status": "success", "saved_message": sent}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_saved_messages(
    limit: int = 10,
) -> str:
    """
    Retrieves recent messages from your personal Telegram 'Saved Messages' cloud chat.
    """
    try:
        msgs = await telegram_service.get_saved_messages(limit=limit)
        return json.dumps({"status": "success", "count": len(msgs), "messages": msgs}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_download_profile_photo(
    bot_username: str,
    output_dir: Optional[str] = None,
) -> str:
    """
    Downloads the profile photo or avatar of any user, bot, or group for visual inspection by vision models.
    """
    try:
        res = await telegram_service.download_profile_photo(bot_username=bot_username, output_dir=output_dir)
        return json.dumps({"status": "success", "result": res}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_send_location(
    bot_username: str,
    latitude: float,
    longitude: float,
    title: Optional[str] = None,
    address: Optional[str] = None,
    provider: Optional[str] = None,
    reply_to_msg_id: Optional[int] = None,
    topic_id: Optional[int] = None,
) -> str:
    """
    Sends geographic coordinates (lat/long) or a named venue to a bot or chat.
    Useful for testing location-aware bots (delivery, weather, transit, check-in).
    """
    try:
        sent = await telegram_service.send_location(
            bot_username=bot_username,
            latitude=latitude,
            longitude=longitude,
            title=title,
            address=address,
            provider=provider,
            reply_to_msg_id=reply_to_msg_id,
            topic_id=topic_id,
        )
        return json.dumps({"status": "success", "sent_location": sent}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_user_profile(
    user_identifier: str,
) -> str:
    """
    Retrieves full profile metadata for a user or bot: biography/about, Telegram Premium status,
    verification badge, scam/fake flags, and mutual groups count.
    """
    try:
        profile = await telegram_service.get_user_profile(user_identifier=user_identifier)
        return json.dumps({"status": "success", "user_profile": profile}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_participant_permissions(
    chat_identifier: str,
    user_identifier: str,
) -> str:
    """
    Inspects granular administrator rights or banned/restricted rights for a user or bot in a channel/group.
    """
    try:
        perms = await telegram_service.get_participant_permissions(
            chat_identifier=chat_identifier,
            user_identifier=user_identifier,
        )
        return json.dumps({"status": "success", "permissions": perms}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_block_peer(
    peer_identifier: str,
) -> str:
    """
    Blocks a user or bot from contacting you.
    """
    try:
        res = await telegram_service.block_peer(peer_identifier=peer_identifier)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_unblock_peer(
    peer_identifier: str,
) -> str:
    """
    Unblocks a previously blocked user or bot.
    """
    try:
        res = await telegram_service.unblock_peer(peer_identifier=peer_identifier)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_blocked_peers(
    limit: int = 50,
) -> str:
    """
    Retrieves the list of currently blocked users and bots.
    """
    try:
        blocked = await telegram_service.get_blocked_peers(limit=limit)
        return json.dumps({"status": "success", "count": len(blocked), "blocked_peers": blocked}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_get_dialog_filters() -> str:
    """
    Retrieves configured Telegram chat folders/filters (e.g. Work, Bots, Personal)
    with their folder IDs, titles, and rule counts.
    """
    try:
        filters = await telegram_service.get_dialog_filters()
        return json.dumps({"status": "success", "count": len(filters), "dialog_filters": filters}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_create_dialog_filter(
    title: str,
    emoticon: Optional[str] = None,
    filter_id: Optional[int] = None,
    contacts: bool = False,
    non_contacts: bool = False,
    groups: bool = False,
    broadcasts: bool = False,
    bots: bool = False,
    exclude_muted: bool = False,
    exclude_read: bool = False,
    exclude_archived: bool = False,
) -> str:
    """
    Creates a new Telegram chat folder/filter (e.g., Bots, Work, Crypto) to organize conversations.
    """
    try:
        res = await telegram_service.create_dialog_filter(
            title=title,
            emoticon=emoticon,
            filter_id=filter_id,
            contacts=contacts,
            non_contacts=non_contacts,
            groups=groups,
            broadcasts=broadcasts,
            bots=bots,
            exclude_muted=exclude_muted,
            exclude_read=exclude_read,
            exclude_archived=exclude_archived,
        )
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_delete_dialog_filter(
    filter_id: int,
) -> str:
    """
    Deletes a Telegram chat folder/filter by its folder ID.
    """
    try:
        res = await telegram_service.delete_dialog_filter(filter_id=filter_id)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_create_chat(
    title: str,
    about: Optional[str] = None,
    megagroup: bool = True,
    for_forum: bool = False,
) -> str:
    """
    Creates a new supergroup or broadcast channel for testing workflows or bot integrations.
    """
    try:
        chat = await telegram_service.create_chat(
            title=title,
            about=about,
            megagroup=megagroup,
            for_forum=for_forum,
        )
        return json.dumps(chat, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_delete_chat(
    chat_identifier: str,
) -> str:
    """
    Permanently deletes a supergroup or channel (must be creator/owner).
    """
    try:
        res = await telegram_service.delete_chat(chat_identifier=chat_identifier)
        return json.dumps(res, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool()
async def telegram_create_invite_link(
    chat_identifier: str,
    title: Optional[str] = None,
    expire_in_seconds: Optional[int] = None,
    expire_date_iso: Optional[str] = None,
    usage_limit: Optional[int] = None,
    request_needed: bool = False,
) -> str:
    """
    Creates a new invite link for a chat or channel with optional expiration, usage limit, and approval requirement.
    """
    try:
        link_data = await telegram_service.create_invite_link(
            chat_identifier=chat_identifier,
            title=title,
            expire_in_seconds=expire_in_seconds,
            expire_date_iso=expire_date_iso,
            usage_limit=usage_limit,
            request_needed=request_needed,
        )
        return json.dumps(link_data, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


if __name__ == "__main__":
    def handle_signal(*args):
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    mcp.run()
