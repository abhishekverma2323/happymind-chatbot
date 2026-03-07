import os
import json
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

# -------------------------
# Load environment variables
# -------------------------
load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
LOCATION = "us-central1"
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

# -------------------------
# Initialize Vertex AI
# -------------------------
from google.oauth2 import service_account

credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

credentials = service_account.Credentials.from_service_account_info(
    json.loads(credentials_json)
)

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    credentials=credentials
)

# Friend-like system prompt
SYSTEM_PROMPT = """
You are HappyMind.

You are NOT an AI assistant.
You are a calm, supportive human friend having a conversation.

Your personality:
- warm
- emotionally intelligent
- patient
- never preachy

How you speak:
- casual natural sentences
- like texting a friend
- short replies
- empathetic

Examples of tone:

User: I feel really sad today.
Good response:
"I'm really sorry you're feeling that way. Want to tell me what happened?"

User: I'm angry.
Good response:
"Yeah that sounds really frustrating. What happened?"

Rules:
- Never lecture
- Never sound like a therapist
- Never say "As an AI"
- Keep replies 2–4 sentences
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
# Crisis Detection
# -------------------------
def is_crisis(text):

    text = text.lower()

    crisis_keywords = [
        "suicide",
        "kill myself",
        "end my life",
        "self harm",
        "hurt myself",
        "i want to die"
    ]

    return any(word in text for word in crisis_keywords)


def crisis_response():

    return (
        "I'm really glad you shared that with me. "
        "If you're feeling like harming yourself, please reach out to someone right now. "
        "If you're in India you can call the Kiran Mental Health Helpline at 1800-599-0019. "
        "You don't have to go through this alone."
    )

# -------------------------
# Detect suggestion request
# -------------------------
def wants_suggestions(text):

    text = text.lower()

    triggers = [
        "suggest",
        "recommend",
        "what should i watch",
        "any movie",
        "movie suggestion",
        "suggest movie",
        "suggest movies",
        "suggest music"
    ]

    return any(trigger in text for trigger in triggers)

# -------------------------
# Gemini Suggestions
# -------------------------
def gemini_suggestions(user_message, history):

    conversation = ""

    for msg in history[-8:]:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            conversation += f"User: {content}\n"
        else:
            conversation += f"Friend: {content}\n"
    prompt = f"""
Conversation history:
{conversation}

User request:
{user_message}

Your job is to recommend movies, music, or relaxing activities depending on the user's mood.

Decision rules:

1. If the user already gave a preference
   (example: comedy, action, relaxing),
   immediately give 3 suggestions.

2. Only ask ONE clarification question if the user gave no preference.

3. If the user says things like
   "just suggest", "anything", "now"
   → immediately give suggestions.

4. Never ask more than one question.

Response style:
- 2 to 3 sentences
- natural friendly tone
- no bullet points
"""

    response = model.generate_content(prompt)

    return response.text

# -------------------------
# Gemini Emotional Response
# -------------------------
def gemini_response(user_message, history):

    conversation = ""

    for msg in history[-8:]:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            conversation += f"User: {content}\n"
        else:
            conversation += f"Friend: {content}\n"

    prompt = f"""
You are HappyMind, a caring and emotionally intelligent friend.

Below is the real conversation history. Only use information that actually appears here.

Conversation history:
{conversation}

Respond to the latest user message in the conversation.

Your task:
- Understand how the user feels from their message.
- Respond with empathy.
- Ask one gentle follow-up question.

Important rules:
- Do NOT invent events that the user did not mention.
- Do NOT assume details.
- If something is unclear, ask the user instead.

Style rules:
- Talk like a human friend
- Be warm and curious
- Keep responses 2-3 sentences
- Avoid lectures or psychological explanations

If the user is overwhelmed, stressed, or stuck,
offer one small practical suggestion instead of only asking questions.

If the user expresses anger or strong emotions,
acknowledge the feeling and gently encourage calm reflection
before reacting.

If the user is struggling emotionally (sadness, anger, stress, breakup, anxiety),
offer 2–3 gentle coping ideas that might help them manage the feeling.

Examples of coping ideas:
- talking to a trusted person
- going for a short walk
- writing thoughts in a journal
- breathing exercises
- taking a break from the stressful situation

Sometimes you may reference well-known psychologists, philosophers,
or mental health ideas if it feels natural.

Avoid vague advice like "try to relax".
Give concrete, simple suggestions instead.
"""

    try:
        response = model.generate_content(prompt)
        return response.text

    except Exception as e:
        print("Gemini error:", e)
        return "I'm here with you. Something went wrong on my side."
    
def detect_intent(user_message, history):

    conversation = ""

    for msg in history[-6:]:
        role = msg["role"]
        content = msg["content"]

        if role == "user":
            conversation += f"User: {content}\n"
        else:
            conversation += f"Friend: {content}\n"

    prompt = f"""
Conversation history:
{conversation}

User message:
{user_message}

Classify the user's intent into ONE of these categories:

1. emotional_talk
2. suggestion_request
3. casual_chat

Only return the category name.
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip().lower()

    except:
        return "emotional_talk"

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

    if is_crisis(user_message):

        final_reply = crisis_response()

    else:

       intent = detect_intent(user_message, history)

       if intent == "suggestion_request":

        final_reply = gemini_suggestions(user_message, history)

       else:

        final_reply = gemini_response(user_message, history)

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
