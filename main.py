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

# In-memory session store
user_sessions = {}

app = Client(
    ":memory:",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# States
STATE_WAIT_ORG_CODE_OR_TOKEN = 1
STATE_WAIT_CREDENTIALS = 2
STATE_WAIT_TOKEN = 3
STATE_WAIT_MOCK_ID = 4


def _validate_env():
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
        )


@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    await message.reply(
        "👋 Welcome to Classplus Mock Extractor Bot!\n\n"
        "Use /Cpmock to start extracting your Classplus mock tests."
    )


@app.on_message(filters.command("Cpmock"))
async def cpmock_handler(client: Client, message: Message):
    user_id = message.from_user.id

    user_sessions[user_id] = {
        "state": STATE_WAIT_ORG_CODE_OR_TOKEN
    }

    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Send Authorization Token (Direct Login)")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.reply(
        "Send Organisation Code or choose option:\n\n"
        "- Send Organisation Code as text\n"
        "- Or click 'Send Authorization Token (Direct Login)'",
        reply_markup=keyboard,
    )


@app.on_message(filters.private)
async def message_handler(client: Client, message: Message):

    # Ignore commands already handled elsewhere
    if message.text and message.text.startswith("/"):
        return

    # Reject non-text messages
    if not message.text:
        await message.reply("Please send text messages only.")
        return

    user_id = message.from_user.id
    text = message.text.strip()

    session = user_sessions.get(user_id)

    if not session:
        await message.reply("Please start with /Cpmock command.")
        return

    state = session.get("state")

    # Step 1
    if state == STATE_WAIT_ORG_CODE_OR_TOKEN:

        if text == "Send Authorization Token (Direct Login)":
            session["state"] = STATE_WAIT_TOKEN

            await message.reply(
                "Please send your Authorization Token now:"
            )
            return

        session["org_code"] = text
        session["state"] = STATE_WAIT_CREDENTIALS

        await message.reply(
            "Send credentials in this format:\n\n"
            "`username password`",
            parse_mode=None,
        )
        return

    # Step 2 Token Login
    if state == STATE_WAIT_TOKEN:

        try:
            await message.reply(
                "Verifying authorization token..."
            )

            token = await login_with_token(text)

            session["auth_token"] = token
            session["state"] = STATE_WAIT_MOCK_ID

            mocks = await fetch_mock_list(token)

            if not mocks:
                await message.reply(
                    "No mock tests found."
                )
                user_sessions.pop(user_id, None)
                return

            session["mocks"] = mocks

            await send_mock_list(message, mocks)

        except Exception as e:
            await message.reply(
                f"Error: {str(e)}"
            )

        return

    # Step 3 Username Password Login
    if state == STATE_WAIT_CREDENTIALS:

        try:
            username, password = text.split(
                maxsplit=1
            )
        except ValueError:
            await message.reply(
                "Invalid format.\n\n"
                "`username password`",
                parse_mode="markdown",
            )
            return

        try:
            await message.reply(
                "Logging in..."
            )

            auth_token = await login_with_org_code(
                session["org_code"],
                username,
                password,
            )

            session["auth_token"] = auth_token
            session["state"] = STATE_WAIT_MOCK_ID

            mocks = await fetch_mock_list(auth_token)

            if not mocks:
                await message.reply(
                    "No mock tests found."
                )
                user_sessions.pop(user_id, None)
                return

            session["mocks"] = mocks

            await send_mock_list(message, mocks)

        except Exception as e:
            await message.reply(
                f"Login failed:\n{e}"
            )
            user_sessions.pop(user_id, None)

        return

    # Step 4 Extract Mock
    if state == STATE_WAIT_MOCK_ID:

        mock_id = text

        mocks = session.get("mocks", [])

        if not any(
            str(m.get("id")) == mock_id
            for m in mocks
        ):
            await message.reply(
                "Invalid Mock ID."
            )
            return

        try:
            await message.reply(
                f"Extracting Mock {mock_id}..."
            )

            mock_data = await fetch_mock_details(
                session["auth_token"],
                mock_id,
            )

            html_file = generate_mock_html(
                mock_data
            )

            try:
                await message.reply_document(
                    html_file,
                    caption=f"{mock_data.get('name', 'Mock')} - Offline Mock Test",
                )
            finally:
                cleanup_file(html_file)

            user_sessions.pop(user_id, None)

        except Exception as e:
            await message.reply(
                f"Failed:\n{e}"
            )

        return


async def send_mock_list(
    message: Message,
    mocks: list,
):
    text = "Available Mock Tests:\n\n"

    for mock in mocks:
        text += (
            f"{mock.get('id')} - "
            f"{mock.get('name', 'Mock')}\n"
        )

    text += "\nSend the Mock ID."

    await message.reply(text)


if __name__ == "__main__":
    print("Starting Classplus Mock Extractor Bot...")
    print("API_ID:", API_ID)
    print("API_HASH loaded:", bool(API_HASH))
    print("BOT_TOKEN loaded:", bool(BOT_TOKEN))

    _validate_env()

    app.run()
