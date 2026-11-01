import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Environment variables from Render
TELNYX_API_KEY = os.getenv("TELNYX_API_KEY")
MY_CELL_PHONE = os.getenv("MY_CELL_PHONE", "+13506662625")  # Replace or set in Render env vars

HEADERS = {
    "Authorization": f"Bearer {TELNYX_API_KEY}",
    "Content-Type": "application/json"
}

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json or {}
    event = data.get('data', {})
    event_type = event.get('event_type')
    payload = event.get('payload', {})
    
    call_control_id = payload.get('call_control_id')
    caller_id = payload.get('from')

    # -------------------------------------------------------------
    # 1. INBOUND SMS FORWARDING (Texts sent to Telnyx -> Your Cell)
    # -------------------------------------------------------------
    if event_type == "message.received":
        customer_number = payload.get('from', {}).get('phone_number')
        incoming_text = payload.get('text', '')
        telnyx_number = payload.get('to', [{}])[0].get('phone_number')
        
        # Forward text to your personal cell phone
        sms_payload = {
            "from": telnyx_number,
            "to": MY_CELL_PHONE,
            "text": f"Forwarded SMS from {customer_number}:\n\n\"{incoming_text}\""
        }
        requests.post("https://api.telnyx.com/v2/messages", json=sms_payload, headers=HEADERS)

    # -------------------------------------------------------------
    # 2. VOICE IVR: Answer Call & Present Options
    # -------------------------------------------------------------
    elif event_type == "call.initiated":
        # Answer inbound voice call
        requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/answer", headers=HEADERS)

    elif event_type == "call.answered":
        # Play audio menu and gather DTMF (keypress 1, 2, *, #)
        gather_payload = {
            "audio_url": "https://raw.githubusercontent.com/thekingwhispers/business-ivr-app/main/speedy_delivery.mp3",
            "valid_digits": "12*#",
            "timeout_millis": 5000
        }
        requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/gather_using_audio", json=gather_payload, headers=HEADERS)

    # -------------------------------------------------------------
    # 3. VOICE IVR: Handle Keypress Responses
    # -------------------------------------------------------------
    elif event_type in ["call.dtmf.received", "call.gather.ended"]:
        digit = payload.get('digits') or payload.get('digit')

                        # Option 1: Play custom audio file for Extension 1
        if digit == "1":
            audio_payload = {
                "audio_url": "https://raw.githubusercontent.com/thekingwhispers/business-ivr-app-1/main/audio_1pressed.mp3",
                "target_legs": "self"
            }
            requests.post(
                f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/playback_start",
                json=audio_payload,
                headers=HEADERS
            )


        # Option 2: Send caller an SMS with info & hang up
        elif digit == "2":
            sms_payload = {
                "from": payload.get('to'),
                "to": caller_id,
                "text": "Thanks for reaching out! Save our local hotline details here: https://example.com"
            }
            requests.post("https://api.telnyx.com/v2/messages", json=sms_payload, headers=HEADERS)
            
            # Brief audio notice before disconnecting
            speak_payload = {"payload": "We have sent a text message to your phone. Goodbye!"}
            requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/speak", json=speak_payload, headers=HEADERS)

        # Timeout / No input / Option #: Route to Voicemail
        else:
            record_payload = {
                "format": "mp3",
                "play_beep": True,
                "max_length": 120
            }
            requests.post(f"https://api.telnyx.com/v2/calls/{call_control_id}/actions/record_start", json=record_payload, headers=HEADERS)

    # -------------------------------------------------------------
    # 4. VOICEMAIL-TO-SMS (Send recording link to your cell)
    # -------------------------------------------------------------
    elif event_type == "call.recording.saved":
        recording_url = payload.get('recording_urls', {}).get('mp3')
        
        sms_payload = {
            "from": payload.get('to'),
            "to": MY_CELL_PHONE,
            "text": f"New Voicemail from {caller_id}:\n{recording_url}"
        }
        requests.post("https://api.telnyx.com/v2/messages", json=sms_payload, headers=HEADERS)

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
  
