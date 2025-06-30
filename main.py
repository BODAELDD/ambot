from telethon.sync import TelegramClient, events
from telethon.sessions import StringSession
import asyncio
import os
import requests
import time
import re

# Debug environment variables
print("🔍 Debugging environment variables...")
print(f"API_ID: {'SET' if os.getenv('API_ID') else 'NOT SET'}")
print(f"API_HASH: {'SET' if os.getenv('API_HASH') else 'NOT SET'}")
print(f"STRING_SESSION: {'SET' if os.getenv('STRING_SESSION') else 'NOT SET'}")
print(f"BOT_TOKEN: {'SET' if os.getenv('BOT_TOKEN') else 'NOT SET'}")
print(f"CHANNEL_ID: {'SET' if os.getenv('CHANNEL_ID') else 'NOT SET'}")

# Configuration from environment variables
api_id = int(os.getenv("API_ID", "27758818"))
api_hash = os.getenv("API_HASH", "f618d737aeaa7578fa0fa30c8c5572de")
string_session = os.getenv("STRING_SESSION", "").strip()  # Strip whitespace
channel_username = os.getenv("CHANNEL_USERNAME", "@Mr_SHADY_Trading_Quotex")
webhook_url = os.getenv("WEBHOOK_URL", "https://marisbriedis.app.n8n.cloud/webhook/fd2ddf25-4b6c-4d7b-9ee1-0d927fda2a41")

# Telegram bot and channel details
BOT_TOKEN = os.getenv("BOT_TOKEN", "7760622012:AAH3RBi2tf_DZHUoMt9sgkfJ4knSvg8WsuE")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002568222061"))

# Clean and validate session string
if string_session:
    string_session = string_session.strip()
    while string_session.startswith('='):
        string_session = string_session[1:]
    string_session = string_session.strip()

# Debug the actual values (safely)
print(f"🔍 STRING_SESSION length: {len(string_session) if string_session else 0}")
print(f"🔍 STRING_SESSION starts with: {string_session[:10] if string_session else 'EMPTY'}...")
print(f"🔍 STRING_SESSION ends with: ...{string_session[-10:] if string_session and len(string_session) > 10 else 'EMPTY'}")

# Global variables
sequence = []
last_signal = None

async def send_to_telegram_channel(message):
    """Send message to Telegram channel using bot"""
    if not message or message.strip() == "":
        print("⚠️ Empty message - not sending")
        return None

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Telegram API response: {response.text}")
        return response.json()
    except Exception as e:
        print(f"❌ Error sending to Telegram channel: {str(e)}")
        return None


def is_valid_session_string(session_str):
    """Validate if the session string looks correct - more lenient validation"""
    if not session_str or len(session_str) < 200:
        print(f"❌ Session string is missing or too short.")
        return False
    if not session_str.startswith('1'):
        print(f"❌ Session string doesn't start with '1'. It might be invalid.")
        return False
    print("✅ Session string format looks valid")
    return True


async def test_session_connection(client):
    """Test if the session can connect and is authorized"""
    try:
        print("🔗 Testing session connection...")
        await client.connect()
        if not await client.is_user_authorized():
            print("❌ Session is not authorized")
            return False
        me = await client.get_me()
        print(f"✅ Session is valid! Connected as: {me.first_name} (@{me.username})")
        return True
    except Exception as e:
        print(f"❌ Session connection test failed: {str(e)}")
        return False


async def main():
    print("📡 Starting Telegram Bot...")
    print(f"📡 Listening for messages on {channel_username}...")
    
    client = None
    if string_session and is_valid_session_string(string_session):
        print("🔐 Attempting to use string session...")
        try:
            client = TelegramClient(StringSession(string_session), api_id, api_hash)
            if not await test_session_connection(client):
                await client.disconnect()
                client = None
        except Exception as e:
            print(f"❌ Error creating client with string session: {str(e)}")
            client = None
    else:
        print("❌ No valid session string provided")
    
    if client is None:
        print("⚠️ Cannot proceed without a valid session. Please check your STRING_SESSION variable.")
        return

    # --- NEW: Regex to parse the specific signal format ---
    # This pattern will capture the asset, timeframe, time, and direction.
    signal_pattern = re.compile(
        r"💳\s*(?P<asset>[\w-]+)\s*"        # Capture asset like "EURGBP-OTC"
        r"🔥\s*(?P<timeframe>\w+)\s*"       # Capture timeframe like "M1"
        r"⌛\s*(?P<time>\d{2}:\d{2}:\d{2})\s*" # Capture time like "18:21:00"
        r"(?P<direction_emoji>[🔼🔽])\s*(?P<direction_text>call|put)", # Capture direction
        re.IGNORECASE | re.MULTILINE
    )

    @client.on(events.NewMessage(chats=channel_username))
    async def handler(event):
        global sequence, last_signal

        message_text = event.message.message.strip()
        print(f"\n📨 Original message received:\n---\n{message_text}\n---")

        # 1. Check for WIN/LOSS/DOJI messages first
        if "WIN" in message_text:
            win_type = "regular"
            if "✅¹" in message_text or "WIN¹" in message_text: win_type = "win1"
            elif "✅²" in message_text or "WIN²" in message_text: win_type = "win2"
            
            print(f"✅ Detected: {win_type.upper()} WIN")
            sequence.append("win")
            
            result_message = {
                "regular": "🚨 AMO QUOTEX BOT 🚨\n✅ WIN",
                "win1": "🚨 AMO QUOTEX BOT 🚨\n✅¹ WIN",
                "win2": "🚨 AMO QUOTEX BOT 🚨\n✅² WIN"
            }.get(win_type)
            
            await send_to_telegram_channel(result_message)
            return

        if "Loss" in message_text or "LOSE" in message_text:
            print("✖️ Detected: Loss")
            sequence.append("loss")
            await send_to_telegram_channel("🚨 AMO QUOTEX BOT 🚨\n💔 LOSS")
            return

        if "DOJI" in message_text:
            print("⚖️ Detected: DOJI - ignoring")
            return

        # 2. Try to parse it as a trading signal using our new regex
        signal_match = signal_pattern.search(message_text)
        if signal_match:
            print("📈 Detected a trading signal. Parsing...")
            
            # Extract data from the regex match
            data = signal_match.groupdict()
            asset = data.get('asset')
            timeframe = data.get('timeframe')
            signal_time = data.get('time')
            direction = data.get('direction_text', '').upper()
            
            # Create a new, clean message
            formatted_message = f"""🚨 AMO QUOTEX BOT 🚨

@amotradingteam - join channel now! 👈

Asset: {asset}
Time: {signal_time}
Timeframe: {timeframe}
Direction: {direction}"""

            print(f"🔄 Reformatted message:\n---\n{formatted_message}\n---")
            await send_to_telegram_channel(formatted_message)
            
            sequence.append("signal")
            last_signal = formatted_message
            return

        # 3. If it's none of the above, ignore it
        print("⚠️ Message does not match any known format (Signal, Win, Loss, Doji). Ignoring.")

        # Sequence management (This logic is preserved from your original code)
        if len(sequence) > 12:
            sequence.pop(0)

        if sequence and sequence[-1] == "win" and sequence.count("win") >= 6: 
            if all(s == "win" for s in sequence[-6:]): 
                print("🔥 Detected 6 consecutive wins. Sending webhook...")
                try:
                    requests.post(webhook_url, json={"message": "6 consecutive trading wins detected!"})
                    print("✅ Webhook sent.")
                except Exception as e:
                    print("❌ Webhook failed:", str(e))
                sequence = [] # Reset sequence after webhook

    try:
        print("🚀 Starting client...")
        if not client.is_connected():
            await client.start()
        print("✅ Bot started successfully!")
        print("👂 Listening for messages...")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Error running bot: {str(e)}")
        raise
    finally:
        if client and client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
