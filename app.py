import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

TELNYX_API_KEY = os.environ.get("TELNYX_API_KEY")
AUDIO_URL = "https://raw.githubusercontent.com/thekingwhispers/business-ivr-app/main/speedy_delivery.mp3"


@app.route("/")
def home():
  return "IVR Bot is online!", 200


@app.route("/webhook", methods=["POST"])
def webhook():
  data = request.json
  event_type = data.get("data", {}).get("event_type")
  payload = data.get("data", {}).get("payload", {})

  # When a call starts ringing your toll-free number
  if event_type == "call.initiated":
    call_control_id = payload.get("call_control_id")

    # Answer the call automatically
    answer_url = (
        f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/answer"
    )
    headers = {
        "Authorization": f"Bearer {TELNYX_API_KEY}",
        "Content-Type": "application/json",
    }
    requests.post(answer_url, headers=headers)

  # Once the call is officially answered, play your custom audio file
  elif event_type == "call.answered":
    call_control_id = payload.get("call_control_id")

    playback_url = (
        f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/playback_start"
    )
    headers = {
        "Authorization": f"Bearer {TELNYX_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {"audio_url": AUDIO_URL}
    response = requests.post(playback_url, json=body, headers=headers)
    print("Playback response:", response.status_code, response.text)

  return jsonify({"status": "success"}), 200


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  
