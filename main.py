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
channel_username = os.getenv("CHANNEL_USERNAME", "@@PocketSignalsM1")
webhook_url = os.getenv("WEBHOOK_URL", "https://marisbriedis.app.n8n.cloud/webhook/fd2ddf25-4b6c-4d7b-9ee1-0d927fda2a41")

# Telegram bot and channel details
BOT_TOKEN = os.getenv("BOT_TOKEN", "7711621476:AAHPgGsxmviRFIRSHtZ8FlQdPdH7lbhrzuM")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1002383089858"))

# Clean and validate session string
if string_session:
    # Remove any leading/trailing whitespace and common prefixes that might be added
    string_session = string_session.strip()
    # Remove any leading = characters
    while string_session.startswith('='):
        string_session = string_session[1:]
    string_session = string_session.strip()  # Strip again after removing =

# Debug the actual values (safely)
print(f"🔍 STRING_SESSION length: {len(string_session) if string_session else 0}")
print(f"🔍 STRING_SESSION starts with: {string_session[:10] if string_session else 'EMPTY'}...")
print(f"🔍 STRING_SESSION ends with: ...{string_session[-10:] if string_session and len(string_session) > 10 else 'EMPTY'}")

# Global variables
sequence = []
last_signal = None

def reformat_signal_message(original_message, is_result=False, win_type=None):
    """Reformat the message to the desired format"""
    if is_result:
        if win_type == "regular":
            return "🚨 AMO QUOTEX BOT 🚨\n✅ WIN"
        elif win_type == "win1":
            return "🚨 AMO QUOTEX BOT 🚨\n✅¹ WIN"
        elif win_type == "win2":
            return "🚨 AMO QUOTEX BOT 🚨\n✅² WIN"
        elif win_type == "loss":
            return "🚨 AMO QUOTEX BOT 🚨\n💔 LOSS"
        return None

    # Split the original message into lines
    lines = original_message.split('\n')

    # Extract the relevant lines - updated to look for new format
    keep_lines = []
    for line in lines:
        if any(prefix in line for prefix in ['🛰', '💷', '💎', '⌚️', '🔼', '🔽']):
            keep_lines.append(line)

    # Construct the new message
    new_message = "🚨 AMO QUOTEX BOT 🚨\n\n"
    new_message += "@amotradingteam - join channel now! 👈\n\n"
    new_message += "\n".join(keep_lines)

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
    if not session_str:
        return False
    
    # Session strings should be at least 200 characters long
    if len(session_str) < 200:
        print(f"❌ Session string too short: {len(session_str)} characters")
        return False
    
    # Should start with "1" (Telethon session format)
    if not session_str.startswith('1'):
        print(f"❌ Session string doesn't start with '1': starts with '{session_str[:5]}'")
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
            
        # Try to get basic info to verify the session works
        me = await client.get_me()
        print(f"✅ Session is valid! Connected as: {me.first_name} (@{me.username})")
        return True
        
    except Exception as e:
        print(f"❌ Session connection test failed: {str(e)}")
        return False


async def main():
    print("📡 Starting Telegram Bot...")
    print(f"📡 Listening for messages on {channel_username}...")
    
    # Initialize client - use session string if available and valid
    client = None
    
    if string_session and is_valid_session_string(string_session):
        print("🔐 Attempting to use string session...")
        try:
            client = TelegramClient(StringSession(string_session), api_id, api_hash)
            
            # Test the session
            if await test_session_connection(client):
                print("✅ String session is working!")
            else:
                print("❌ String session failed authorization test")
                await client.disconnect()
                client = None
                
        except Exception as e:
            print(f"❌ Error creating client with string session: {str(e)}")
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
            client = None
    else:
        print("❌ No valid session string provided")
    
    # If string session failed, we can't proceed in Railway
    if client is None:
        print("📁 No valid session available...")
        print("⚠️ Cannot create new session in Railway environment (no interactive input).")
        print()
        print("🔧 To fix this issue:")
        print("1. Make sure you're using the COMPLETE session string from generate_session.py")
        print("2. The session string should be around 350+ characters long")
        print("3. It should start with '1BJWap1w...' or similar")
        print("4. Make sure there are no extra spaces or characters when copying")
        print("5. In Railway, go to Variables tab and update STRING_SESSION")
        print("6. Redeploy the application")
        print()
        print("💡 Try running generate_session.py again to get a fresh session string")
        return

    @client.on(events.NewMessage(chats=channel_username))
    async def handler(event):
        global sequence, last_signal

        message_text = event.message.message.strip()
        print(f"📨 Original message: {message_text}")

        # Handle WIN messages
        win_match = re.search(r"WIN\s*(✅\d*)", message_text)
        if win_match:
            sequence.append("win")
            win_type = "regular"
            if "✅¹" in message_text:
                win_type = "win1"
                print("✅¹ Detected: WIN 1")
            elif "✅²" in message_text:
                win_type = "win2"
                print("✅² Detected: WIN 2")
            else:
                print("✅ Detected: WIN")
            
            result_message = reformat_signal_message(None, True, win_type)
            await send_to_telegram_channel(result_message)
            return
            
        # Handle Loss messages
        if "✖️ Loss" in message_text:
            sequence.append("loss")
            print("✖️ Detected: Loss")
            result_message = reformat_signal_message(None, True, "loss")
            await send_to_telegram_channel(result_message)
            return
            
        # Handle DOJI messages
        if "DOJI ⚖" in message_text:
            print("⚖️ Detected: DOJI - ignoring")
            return

        # Process trading signals - updated to detect new format
        # Check if message contains the new signal format
        if ("🛰 POCKET OPTION" in message_text and 
            any(indicator in message_text for indicator in ['🔼 call', '🔽 put']) and
            any(currency in message_text for currency in ['💷', '💰', '💵', '💴', '💶'])):
            
            formatted_message = reformat_signal_message(message_text)
            
            if formatted_message:
                print(f"🔄 Reformatted message: {formatted_message}")
                await send_to_telegram_channel(formatted_message)
                sequence.append("call")
                last_signal = formatted_message  # Store the last signal
                print("📈 Detected: SIGNAL CALL")
            else:
                print("⚠️ Not a valid signal format - ignoring")
        else:
            print("⚠️ Message doesn't match new signal format - ignoring")

        # Sequence management
        if len(sequence) > 12:
            sequence.pop(0)

        if sequence == ["call", "win"] * 6:
            print("🔥 Detected 6 consecutive SIGNAL → WIN pairs. Sending webhook...")
            try:
                requests.post(webhook_url, json={"message": "6 consecutive trading wins detected on M5!"})
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
