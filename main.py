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
channel_username = os.getenv("CHANNEL_USERNAME", "@quotex24x7signalsbot")
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

def create_new_format_signal(asset, timeframe, signal_time, direction):
    """
    Creates a signal message in the new desired format.
    Example output:
    📉GBPJPY-OTC↗️

    ⏱️UTC +5:30⏱️

    🎯 1 MIN TRADE 🐷

    ⏱️02:08 - CALL↗️
    """
    # Determine direction text and icons
    if 'put' in direction.lower() or 'sell' in direction.lower():
        dir_text = "PUT"
        dir_icon_main = "📉"
        dir_icon_arrow = "↘️"
    else: # Default to call/buy
        dir_text = "CALL"
        dir_icon_main = "📈"
        dir_icon_arrow = "↗️"
        
    # Format the timeframe
    timeframe_text = timeframe.replace('M', '') + " MIN TRADE"
    
    # Format the time (extract HH:MM from HH:MM:SS)
    formatted_time = signal_time[:5]

    # Assemble the new message
    new_message = (
        f"{dir_icon_main}{asset}{dir_icon_arrow}\n\n"
        f"⏱️UTC +5:30⏱️\n\n"
        f"🎯 {timeframe_text} 🐷\n\n"
        f"⏱️{formatted_time} - {dir_text}{dir_icon_arrow}"
    )
    
    return new_message


async def send_to_telegram_channel(message):
    """Send message to Telegram channel using bot"""
    if not message or message.strip() == "":
        print("⚠️ Empty message - not sending")
        return None

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": message,
        "parse_mode": "HTML" # Can be changed to Markdown if needed
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
        print(f"❌ Session string too short or empty")
        return False
    if not session_str.startswith('1'):
        print(f"❌ Session string doesn't start with '1'")
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
    
    client = None
    if string_session and is_valid_session_string(string_session):
        print("🔐 Attempting to use string session...")
        try:
            client = TelegramClient(StringSession(string_session), api_id, api_hash)
            if not await test_session_connection(client):
                print("❌ String session failed authorization test, cannot proceed.")
                await client.disconnect()
                return
        except Exception as e:
            print(f"❌ Error creating client with string session: {str(e)}")
            return
    else:
        print("❌ No valid session string provided. Cannot proceed.")
        return

    print(f"📡 Listening for messages on {channel_username}...")

    @client.on(events.NewMessage(chats=channel_username))
    async def handler(event):
        global sequence, last_signal

        message_text = event.message.message.strip()
        print(f"\n📨 Original message received:\n---\n{message_text}\n---")

        # --- NEW: Handle Result Messages ---
        if "💰 MTG WIN 💰" in message_text:
            print("✅ Detected: MTG WIN")
            sequence.append("win")
            await send_to_telegram_channel("💰 MTG WIN 💰")
            return

        if "💰 WIN 💰" in message_text:
            print("✅ Detected: WIN")
            sequence.append("win")
            await send_to_telegram_channel("💰 WIN 💰")
            return

        if "📉 LOSS 📉" in message_text:
            print("❌ Detected: LOSS")
            sequence.append("loss")
            await send_to_telegram_channel("📉 LOSS 📉")
            return
            
        # Handle other non-signal messages
        if "DOJI ⚖" in message_text or "CANCEL" in message_text:
            print("⚖️ Detected: DOJI/CANCEL - ignoring")
            return

        # --- NEW: Handle and Reformat Trading Signals ---
        # Regex to parse the OLD signal format
        signal_pattern = re.compile(
            r"💳\s*(?P<asset>.*?)\n"
            r".*?🔥\s*(?P<timeframe>M\d+)\n"
            r".*?⌛️\s*(?P<time>\d{2}:\d{2}:\d{2})\n"
            r".*?(?P<direction>🔽 put|🔼 call)",
            re.DOTALL | re.IGNORECASE
        )
        
        match = signal_pattern.search(message_text)
        
        if match:
            # Extract data from the old format
            data = match.groupdict()
            asset = data['asset'].strip()
            timeframe = data['timeframe'].strip()
            signal_time = data['time'].strip()
            direction = data['direction'].strip()

            print(f"📈 Detected old signal format: Asset={asset}, Timeframe={timeframe}, Time={signal_time}, Direction={direction}")

            # Create the new formatted message
            new_message = create_new_format_signal(asset, timeframe, signal_time, direction)
            
            print(f"🔄 Reformatted message:\n---\n{new_message}\n---")
            await send_to_telegram_channel(new_message)
            
            sequence.append("signal")
            last_signal = new_message
        else:
            print("⚠️ Message doesn't match any known signal or result format - ignoring.")

        # Sequence management for webhooks
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
                sequence = []

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
