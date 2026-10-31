import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

TELNYX_API_KEY = os.environ.get("TELNYX_API_KEY")
AUDIO_URL = "https://your-username.github.io/your-repo/greeting.mp3"  # Update later with your GitHub Pages link


@app.route("/webhook", methods=["POST"])
def telnyx_webhook():
  data = request.json.get("data", {})
  event_type = data.get("event_type")
  payload = data.get("payload", {})
  call_control_id = payload.get("call_control_id")

  headers = {
      "Authorization": f"Bearer {TELNYX_API_KEY}",
      "Content-Type": "application/json",
  }

  # Answer incoming call
  if event_type == "call.initiated":
    url = f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/answer"
    requests.post(url, headers=headers)

  # Play greeting audio on connection
  elif event_type == "call.answered":
    url = (
        f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/playback_start"
    )
    body = {"audio_url": AUDIO_URL, "loop": 1}
    requests.post(url, headers=headers, json=body)

  return jsonify({"status": "success"}), 200


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
  
