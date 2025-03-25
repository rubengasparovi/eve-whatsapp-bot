from flask import Flask, request
import requests
import base64
import json
import os

app = Flask(__name__)

# Load API keys and secrets from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")

# In-memory session store
user_sessions = {}


@app.route('/whatsapp', methods=['POST'])
def whatsapp_bot():
    from_number = request.form.get('From')
    media_url = request.form.get('MediaUrl0')
    body = request.form.get('Body', '').strip()

    if from_number not in user_sessions:
        if media_url:
            user_sessions[from_number] = {"image_url": media_url}
            return respond("What are you interested regarding this picture?")
        else:
            return respond("Please send me a photo to get started.")
    else:
        prompt = body
        image_url = user_sessions[from_number].get("image_url")
        del user_sessions[from_number]

        gemini_reply = process_image_with_gemini(prompt, image_url)
        return respond(gemini_reply)


def process_image_with_gemini(prompt, image_url):
    print("📥 Prompt:", prompt)
    print("🌐 Image URL:", image_url)

    # Step 1: Download image with Twilio credentials
    try:
        image_response = requests.get(image_url, auth=(TWILIO_SID, TWILIO_AUTH))
        print("📥 Image download status:", image_response.status_code)
        image_response.raise_for_status()
        image_bytes = image_response.content
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    except Exception as e:
        print("❌ Image download failed:", str(e))
        return "Sorry, I couldn't download the image."

    # Step 2: Prepare Gemini request
    headers = {
        "Content-Type": "application/json"
    }

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_base64
                        }
                    }
                ]
            }
        ]
    }

    # Step 3: Call Gemini API
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print("📡 Gemini response status:", response.status_code)
        print("📨 Gemini raw response:", response.text)

        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Gemini couldn't process the image: {response.text}"
    except Exception as e:
        print("❌ Gemini API error:", str(e))
        return "Sorry, something went wrong while talking to Gemini."


def respond(message):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""
