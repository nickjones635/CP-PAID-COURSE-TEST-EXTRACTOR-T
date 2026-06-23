import os
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from utils import (
    login_with_org_code,
    login_with_token,
    fetch_mock_list,
    fetch_mock_details,
    generate_mock_html,
    cleanup_file,
)
from config import API_ID, API_HASH, BOT_TOKEN

# Simple in-memory user session store
user_sessions = {}

app = Client("classplus_mock_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# States for conversation
STATE_WAIT_ORG_CODE_OR_TOKEN = 1
STATE_WAIT_CREDENTIALS = 2
STATE_WAIT_TOKEN = 3
STATE_WAIT_MOCK_ID = 4


def _validate_env() -> None:
    # Keep a friendly error for common misconfig.
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Create a .env file (see .env.example) or set them in your environment."
        )

@ app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    text = (
        "👋 Welcome to Classplus Mock Extractor Bot!\n\n"
        "Use /Cpmock to start extracting your Classplus mock tests."
    )
    await message.reply(text)


@ app.on_message(filters.command("Cpmock"))
async def cpmock_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {"state": STATE_WAIT_ORG_CODE_OR_TOKEN}
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Send Authorization Token (Direct Login)")],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    await message.reply(
        "Send me Organisation Code or choose option:\n\n"
        "- Send Organisation Code as text\n"
        "- Or click on 'Send Authorization Token (Direct Login)' button",
        reply_markup=keyboard,
    )


import os
from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from utils import (
    login_with_org_code,
    login_with_token,
    fetch_mock_list,
    fetch_mock_details,
    generate_mock_html,
    cleanup_file,
)
from config import API_ID, API_HASH, BOT_TOKEN

# Simple in-memory user session store
user_sessions = {}

app = Client("classplus_mock_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# States for conversation
STATE_WAIT_ORG_CODE_OR_TOKEN = 1
STATE_WAIT_CREDENTIALS = 2
STATE_WAIT_TOKEN = 3
STATE_WAIT_MOCK_ID = 4


def _validate_env() -> None:
    # Keep a friendly error for common misconfig.
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Create a .env file (see .env.example) or set them in your environment."
        )

@ app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    text = (
        "👋 Welcome to Classplus Mock Extractor Bot!\n\n"
        "Use /Cpmock to start extracting your Classplus mock tests."
    )
    await message.reply(text)


@ app.on_message(filters.command("Cpmock"))
async def cpmock_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_sessions[user_id] = {"state": STATE_WAIT_ORG_CODE_OR_TOKEN}
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Send Authorization Token (Direct Login)")],
        ],
        one_time_keyboard=True,
        resize_keyboard=True,
    )
    await message.reply(
        "Send me Organisation Code or choose option:\n\n"
        "- Send Organisation Code as text\n"
        "- Or click on 'Send Authorization Token (Direct Login)' button",
        reply_markup=keyboard,
    )


@app.on_message(filters.private)
async def message_handler(client: Client, message: Message):

    if not message.text:
        await message.reply("Please send text messages only.")
        return

    if message.text.startswith("/"):
        return

    text = message.text.strip()

    user_id = message.from_user.id
    session = user_sessions.get(user_id)

    # rest of your existing code...
async def message_handler(client: Client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()
    session = user_sessions.get(user_id)

    if not session:
        await message.reply("Please start with /Cpmock command.")
        return

    state = session.get("state")

    if state == STATE_WAIT_ORG_CODE_OR_TOKEN:
        if text == "Send Authorization Token (Direct Login)":
            await message.reply("Please send your Authorization Token now:", reply_markup=None)
            session["state"] = STATE_WAIT_TOKEN
            return

        # Assume user sent org code
        session["org_code"] = text
        session["state"] = STATE_WAIT_CREDENTIALS
        await message.reply("Send your login credentials in format:\n\n`username password`", parse_mode="markdown")
        return

    if state == STATE_WAIT_TOKEN:
        # User sent authorization token directly
        auth_token = text
        await message.reply("Verifying authorization token, please wait...", reply_markup=None)
        try:
            token = await login_with_token(auth_token)
            session["auth_token"] = token
            session["state"] = STATE_WAIT_MOCK_ID
            await message.reply("Token verified! Fetching your mock tests...")
            mocks = await fetch_mock_list(token)
            if not mocks:
                await message.reply("No mock tests found in your account.")
                user_sessions.pop(user_id)
                return
            session["mocks"] = mocks
            await send_mock_list(message, mocks)
        except Exception as e:
            await message.reply(f"Error: {str(e)}\nPlease send a valid Authorization Token.")
        return

    if state == STATE_WAIT_CREDENTIALS:
        # Expecting username and password
        try:
            username, password = text.split(maxsplit=1)
        except ValueError:
            await message.reply("Invalid format. Please send credentials as:\n\n`username password`", parse_mode="markdown")
            return
        org_code = session.get("org_code")
        await message.reply("Logging in, please wait...", reply_markup=None)
        try:
            auth_token = await login_with_org_code(org_code, username, password)
            session["auth_token"] = auth_token
            session["state"] = STATE_WAIT_MOCK_ID
            await message.reply("Login successful! Fetching your mock tests...")
            mocks = await fetch_mock_list(auth_token)
            if not mocks:
                await message.reply("No mock tests found in your account.")
                user_sessions.pop(user_id)
                return
            session["mocks"] = mocks
            await send_mock_list(message, mocks)
        except Exception as e:
            await message.reply(f"Login failed: {str(e)}\nPlease send Organisation Code again with /Cpmock.")
            user_sessions.pop(user_id)
        return

    if state == STATE_WAIT_MOCK_ID:
        # Expecting mock ID to extract
        mock_id = text
        mocks = session.get("mocks", [])
        if not any(str(m.get("id")) == str(mock_id) for m in mocks):
            await message.reply("Invalid Mock ID. Please send a valid Mock ID from the list.")
            return

        auth_token = session.get("auth_token")
        await message.reply(f"Extracting Mock {mock_id}... Please wait.")
        try:
            mock_data = await fetch_mock_details(auth_token, str(mock_id))
            html_file = generate_mock_html(mock_data)
            # Send file
            await message.reply_document(html_file, caption=f"{mock_data.get('name','Mock')} - Offline Mock Test")
            # Cleanup
            cleanup_file(html_file)
            # End session
            user_sessions.pop(user_id)
        except Exception as e:
            await message.reply(f"Failed to extract mock: {str(e)}")
        return

async def send_mock_list(message: Message, mocks: list):
    text = "Available Mock Tests:\n\n"
    for m in mocks:
        text += f"{m.get('id')} – {m.get('name','Mock')}\n"
    text += "\nSend the Mock ID to start extraction."
    await message.reply(text, reply_markup=None)

if __name__ == "__main__":
    print("Starting Classplus Mock Extractor Bot...")
    _validate_env()
    app.run()


    if not session:
        await message.reply("Please start with /Cpmock command.")
        return

    state = session.get("state")

    if state == STATE_WAIT_ORG_CODE_OR_TOKEN:
        if text == "Send Authorization Token (Direct Login)":
            await message.reply("Please send your Authorization Token now:", reply_markup=None)
            session["state"] = STATE_WAIT_TOKEN
            return

        # Assume user sent org code
        session["org_code"] = text
        session["state"] = STATE_WAIT_CREDENTIALS
        await message.reply("Send your login credentials in format:\n\n`username password`", parse_mode="markdown")
        return

    if state == STATE_WAIT_TOKEN:
        # User sent authorization token directly
        auth_token = text
        await message.reply("Verifying authorization token, please wait...", reply_markup=None)
        try:
            token = await login_with_token(auth_token)
            session["auth_token"] = token
            session["state"] = STATE_WAIT_MOCK_ID
            await message.reply("Token verified! Fetching your mock tests...")
            mocks = await fetch_mock_list(token)
            if not mocks:
                await message.reply("No mock tests found in your account.")
                user_sessions.pop(user_id)
                return
            session["mocks"] = mocks
            await send_mock_list(message, mocks)
        except Exception as e:
            await message.reply(f"Error: {str(e)}\nPlease send a valid Authorization Token.")
        return

    if state == STATE_WAIT_CREDENTIALS:
        # Expecting username and password
        try:
            username, password = text.split(maxsplit=1)
        except ValueError:
            await message.reply("Invalid format. Please send credentials as:\n\n`username password`", parse_mode="markdown")
            return
        org_code = session.get("org_code")
        await message.reply("Logging in, please wait...", reply_markup=None)
        try:
            auth_token = await login_with_org_code(org_code, username, password)
            session["auth_token"] = auth_token
            session["state"] = STATE_WAIT_MOCK_ID
            await message.reply("Login successful! Fetching your mock tests...")
            mocks = await fetch_mock_list(auth_token)
            if not mocks:
                await message.reply("No mock tests found in your account.")
                user_sessions.pop(user_id)
                return
            session["mocks"] = mocks
            await send_mock_list(message, mocks)
        except Exception as e:
            await message.reply(f"Login failed: {str(e)}\nPlease send Organisation Code again with /Cpmock.")
            user_sessions.pop(user_id)
        return

    if state == STATE_WAIT_MOCK_ID:
        # Expecting mock ID to extract
        mock_id = text
        mocks = session.get("mocks", [])
        if not any(str(m.get("id")) == str(mock_id) for m in mocks):
            await message.reply("Invalid Mock ID. Please send a valid Mock ID from the list.")
            return

        auth_token = session.get("auth_token")
        await message.reply(f"Extracting Mock {mock_id}... Please wait.")
        try:
            mock_data = await fetch_mock_details(auth_token, str(mock_id))
            html_file = generate_mock_html(mock_data)
            # Send file
            await message.reply_document(html_file, caption=f"{mock_data.get('name','Mock')} - Offline Mock Test")
            # Cleanup
            cleanup_file(html_file)
            # End session
            user_sessions.pop(user_id)
        except Exception as e:
            await message.reply(f"Failed to extract mock: {str(e)}")
        return

async def send_mock_list(message: Message, mocks: list):
    text = "Available Mock Tests:\n\n"
    for m in mocks:
        text += f"{m.get('id')} – {m.get('name','Mock')}\n"
    text += "\nSend the Mock ID to start extraction."
    await message.reply(text, reply_markup=None)

if __name__ == "__main__":
    print("Starting Classplus Mock Extractor Bot...")
    _validate_env()
    app.run()
