import os
import json
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel
from google.oauth2 import service_account

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = "us-central1"
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# -------------------------
# Vertex AI Authentication (for deployment)
# -------------------------
credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

credentials = service_account.Credentials.from_service_account_info(
    json.loads(credentials_json)
)

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    credentials=credentials
)

# -------------------------
# System Prompt
# -------------------------
SYSTEM_PROMPT = """
You are HappyMind.

You are NOT an AI assistant.
You are a calm, supportive human friend having a conversation.

Personality:
- warm
- emotionally intelligent
- patient
- casual tone

Rules:
- never lecture
- never say "as an AI"
- never sound like a therapist
- speak like a real friend
- responses should be 2–4 sentences
"""

model = GenerativeModel(
    "gemini-2.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# -------------------------
# Flask App
# -------------------------
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY


# -------------------------
# SAFETY LAYER
# -------------------------
def detect_self_harm(text):

    patterns = [
        "suicide",
        "kill myself",
        "end my life",
        "self harm",
        "hurt myself",
        "i want to die"
    ]

    return any(p in text.lower() for p in patterns)


def detect_violence(text):

    patterns = [
        "i killed",
        "i murdered",
        "i stabbed",
        "i shot someone",
        "i hurt someone"
    ]

    return any(p in text.lower() for p in patterns)


def self_harm_response():

    return (
        "I'm really glad you told me. If you're feeling like harming yourself, "
        "please reach out to someone right now. If you're in India you can call "
        "the Kiran Mental Health Helpline at 1800-599-0019. You don't have to go through this alone."
    )


def violence_response():

    return (
        "That sounds like a very serious situation. I can't help with anything related to harming someone. "
        "The best step would be to contact local authorities or emergency services."
    )


# -------------------------
# EMOTION DETECTION
# -------------------------
def detect_emotion(text):

    text = text.lower()

    if any(w in text for w in ["sad", "depressed", "lonely", "hurt"]):
        return "sadness"

    if any(w in text for w in ["angry", "mad", "furious"]):
        return "anger"

    if any(w in text for w in ["stress", "overwhelmed", "pressure"]):
        return "stress"

    if any(w in text for w in ["anxious", "worried", "panic"]):
        return "anxiety"

    if any(w in text for w in ["happy", "great", "excited"]):
        return "happiness"

    return "neutral"


# -------------------------
# SIMPLE INTENT DETECTION
# -------------------------
def detect_intent(text):

    text = text.lower()

    if "quote" in text or "motivation" in text:
        return "quotes"

    if "music" in text or "song" in text:
        return "music"

    if "suggest" in text or "recommend" in text:
        return "suggestion"

    return "chat"


# -------------------------
# SIMPLE CONTENT RESPONSES
# -------------------------
def motivational_quotes():

    quotes = [
        "The only way to do great work is to love what you do. – Steve Jobs",
        "Believe you can and you're halfway there. – Theodore Roosevelt",
        "Success is not final, failure is not fatal: it is the courage to continue that counts. – Winston Churchill"
    ]

    return "Here are a few motivational quotes I like: " + " | ".join(quotes)


def music_suggestions():

    return (
        "You might like some lo-fi beats, soft piano music, or ambient soundscapes. "
        "Artists like Ludovico Einaudi are great for relaxing."
    )


# -------------------------
# CONTEXT BUILDER
# -------------------------
def build_context(history):

    context = ""

    for msg in history[-10:]:

        if msg["role"] == "user":
            context += f"User: {msg['content']}\n"

        else:
            context += f"Friend: {msg['content']}\n"

    return context


# -------------------------
# Gemini Response
# -------------------------
def gemini_response(user_message, history, emotion):

    context = build_context(history)

    prompt = f"""
Conversation history:
{context}

User message:
{user_message}

Detected emotion: {emotion}

Respond like a real supportive friend.

Guidelines:
- understand the user's situation
- be natural and empathetic
- give helpful advice if needed
- do NOT ask a question every time
- keep responses 2-3 sentences
"""

    try:

        response = model.generate_content(prompt)

        return response.text

    except Exception as e:

        print("Gemini error:", e)

        return "I'm here with you. Something went wrong on my side."


# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():

    session.pop("history", None)

    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():

    user_message = request.json.get("message")

    history = session.get("history", [])

    history.append({
        "role": "user",
        "content": user_message
    })

    # SAFETY CHECKS

    if detect_self_harm(user_message):

        final_reply = self_harm_response()

    elif detect_violence(user_message):

        final_reply = violence_response()

    else:

        intent = detect_intent(user_message)
        emotion = detect_emotion(user_message)

        if intent == "quotes":

            final_reply = motivational_quotes()

        elif intent == "music":

            final_reply = music_suggestions()

        else:

            final_reply = gemini_response(user_message, history, emotion)

    history.append({
        "role": "bot",
        "content": final_reply
    })

    session["history"] = history[-20:]

    return jsonify({"reply": final_reply})


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)
