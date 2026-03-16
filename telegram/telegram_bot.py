import logging
import requests
from telethon.sync import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest


# Replace these with your values
api_id = 29637168         # from https://my.telegram.org
api_hash = '4cd18ea92258cb591cdfa0e08ad114f1'
channel = 'WatcherGuru'  # or full URL without @

# --- DISCORD CONFIG ---
DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1360652670037131295/6KxXXaiwEzn__1Wub25k2mn8AWWKsiVU2Vk7h2nfGtmR79oT4BuI2zRk3bOmIB861KVl"

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- TELEGRAM CLIENT ---
client = TelegramClient('session_name', api_id, api_hash)

def send_to_discord(content):
    payload = {"content": content}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        if response.status_code == 204:
            logging.info("✅ Message sent to Discord")
        else:
            logging.warning(f"⚠️ Failed to send message (status: {response.status_code})")
    except Exception as e:
        logging.error(f"❌ Error sending to Discord: {e}")

@client.on(events.NewMessage(chats=channel))
async def handler(event):
    message = event.message.message
    logging.info(f"📩 New Telegram message: {message}")
    send_to_discord(message)

async def main():
    # Fetch the latest message from the channel
    entity = await client.get_entity(channel)
    history = await client(GetHistoryRequest(
        peer=entity,
        limit=1,
        offset_date=None,
        offset_id=0,
        max_id=0,
        min_id=0,
        add_offset=0,
        hash=0
    ))
    if history.messages:
        last_message = history.messages[0].message
        logging.info(f"📤 Sending latest message on start: {last_message}")
        send_to_discord(last_message)

    logging.info("🚀 Listening for new Telegram messages...")
    await client.run_until_disconnected()

# --- RUN THE CLIENT ---
with client:
    client.loop.run_until_complete(main())
