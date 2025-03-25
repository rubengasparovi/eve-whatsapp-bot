from flask import Flask, request
import requests
import base64
import json
import os

app = Flask(__name__)

GEMINI_API_KEY = os.getenv("AIzaSyCYu359IS6Ay-PZYqRTeRJl-Xp2e76QT64")  # safer than hardcoding

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
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIzaSyCYu359IS6Ay-PZYqRTeRJl-Xp2e76QT64}"
    }

    image_bytes = requests.get(image_url).content
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

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

    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent",
        headers=headers,
        data=json.dumps(data)
    )

    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    else:
        return "Sorry, I couldn't analyze the image."


def respond(message):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{message}</Message>
</Response>"""