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

# --- MODIFIED SECTION: This function is completely updated for the new formats ---
def reformat_signal_message(original_message, is_result=False, win_type=None):
    """
    Reformat the message to the desired signal or result format.
    """
    if is_result:
        # This part handles the new WIN/LOSS/MTG formats
        if win_type == "regular":
            return "💰 WIN 💰"
        elif win_type in ["win1", "win2"]: # Handling Martingale wins
            return "💰 MTG WIN 💰"
        elif win_type == "loss":
            return "📉 LOSS 📉"
        return None # Should not happen

    # --- This part handles the new signal format ---
    # We will parse the original_message to build the new format.
    # Example incoming message format assumed: "Pair: GBPJPY-OTC... Time: 02:08... Direction: CALL..."
    
    # Use regex to find the required pieces of information.
    # This pattern is designed to be flexible with the text around the data.
    asset_match = re.search(r"([A-Z]{6,}(?:-OTC)?)", original_message, re.IGNORECASE)
    time_match = re.search(r"(\d{2}:\d{2})", original_message)
    direction_match = re.search(r"(CALL|PUT|BUY|SELL)", original_message, re.IGNORECASE)
    timeframe_match = re.search(r"(\d+)\s*MIN", original_message, re.IGNORECASE)

    # Check if we found all the necessary parts
    if asset_match and time_match and direction_match and timeframe_match:
        asset = asset_match.group(1).upper()
        signal_time = time_match.group(1)
        direction_text = direction_match.group(1).upper()
        timeframe = timeframe_match.group(1)

        # Determine direction and emoji
        if direction_text in ["CALL", "BUY"]:
            direction_formatted = "CALL↗️"
            asset_formatted = f"📉{asset}↗️"
        elif direction_text in ["PUT", "SELL"]:
            direction_formatted = "PUT↘️"
            asset_formatted = f"📈{asset}↘️"
        else:
            return None # Unknown direction

        # Build the final message string in the desired format
        new_message = (
            f"{asset_formatted}\n"
            f"⏱️UTC +5:30⏱️\n"
            f"🎯 {timeframe} MIN TRADE 🐷\n"
            f"⏱️{signal_time} - {direction_formatted}"
        )
        return new_message
    else:
        # If we can't parse the message, return None so we don't send garbage
        print(f"⚠️ Could not parse signal from: '{original_message}'")
        return None

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
        response_data = response.json()
        if not response_data.get("ok"):
            print(f"❌ Telegram API Error: {response_data.get('description')}")
        else:
            print(f"✅ Message sent successfully to channel {CHANNEL_ID}.")
        return response_data
    except Exception as e:
        print(f"❌ Error sending to Telegram channel: {str(e)}")
        return None

def is_valid_session_string(session_str):
    if not session_str: return False
    if len(session_str) < 200:
        print(f"❌ Session string too short: {len(session_str)} characters")
        return False
    if not session_str.startswith('1'):
        print(f"❌ Session string doesn't start with '1': starts with '{session_str[:5]}'")
        return False
    print("✅ Session string format looks valid")
    return True

async def test_session_connection(client):
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
            if client: await client.disconnect()
            client = None
    
    if client is None:
        print("🔴 CRITICAL: No valid session available. The bot cannot start.")
        print("🔧 Please generate a new STRING_SESSION and set it in your environment variables.")
        return

    # --- MODIFIED SECTION: Handler logic is simplified ---
    @client.on(events.NewMessage(chats=channel_username))
    async def handler(event):
        global sequence, last_signal

        message_text = event.message.message.strip()
        print(f"\n📨 Original message received: '{message_text}'")

        formatted_message = None
        
        # 1. Check for WIN results
        if "WIN" in message_text.upper():
            win_type = "regular"
            if "✅¹" in message_text or "MTG 1" in message_text.upper():
                win_type = "win1"
                print("🔹 Detected: Martingale 1 WIN")
            elif "✅²" in message_text or "MTG 2" in message_text.upper():
                win_type = "win2"
                print("🔹 Detected: Martingale 2 WIN")
            else:
                print("🔹 Detected: Regular WIN")

            sequence.append("win")
            formatted_message = reformat_signal_message(message_text, is_result=True, win_type=win_type)
            
        # 2. Check for LOSS results
        elif "LOSS" in message_text.upper():
            print("🔹 Detected: LOSS")
            sequence.append("loss")
            formatted_message = reformat_signal_message(message_text, is_result=True, win_type="loss")

        # 3. Check for DOJI (ignore)
        elif "DOJI" in message_text.upper():
            print("⚖️ Detected: DOJI - ignoring")
            return

        # 4. If none of the above, assume it's a trading signal and try to format it
        else:
            print("🔹 Detected: Potential Signal")
            sequence.append("signal")
            formatted_message = reformat_signal_message(message_text, is_result=False)
            if formatted_message:
                last_signal = formatted_message # Store the last valid signal

        # 5. Send the formatted message if it was created successfully
        if formatted_message:
            print(f"✅ Formatting successful. Preparing to send:\n---\n{formatted_message}\n---")
            await send_to_telegram_channel(formatted_message)
        else:
            print("⚠️ Message did not match any known format (Signal, Win, Loss) or failed parsing. Ignoring.")

        # --- Sequence management for webhook ---
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
