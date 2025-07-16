import os
import requests

from services import *
from dotenv import load_dotenv
from slack_bolt import App, Ack
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

load_dotenv("tokens.env")

SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"].strip()
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"].strip()
app = App(token=SLACK_BOT_TOKEN)
client = WebClient(token=SLACK_BOT_TOKEN)

@app.event("message")
def handle_message_events(event, say):
    global client
    if event.get("bot_id"):
        return
    if event.get("subtype") == "bot_message":
        return
    files = event.get("files")
    if not files:
        print("No files in this message, skipping.")
        return
    convert_image(event, client)

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()