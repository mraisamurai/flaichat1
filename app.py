from flask import Flask, request, jsonify, render_template, session
import os
import requests
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Azure API Credentials
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")

def clean_response(text):
    """Clean and format AI responses."""
    text = re.sub(r'[#*_~`]', '', text)
    text = re.sub(r'\n\s*\n', '<br><br>', text)
    text = re.sub(r'\s*-\s*', '• ', text)
    return text.strip()

def is_asking_about_foodsliver_ai(message):
    """Check if the user is asking about Foods Liver AI."""
    triggers = [
        "what is foods liver ai",
        "tell me about foods liver ai",
        "explain foods liver ai",
        "what does foods liver ai do",
        "purpose of foods liver ai",
        "foods liver ai?"
    ]
    return any(trigger in message.lower() for trigger in triggers)

@app.route("/")
def index():
    """Render the chat interface."""
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    """Handle chat with context and ad display."""
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Please enter a message."}), 400

    # Predefined response for "What is Foods Liver AI?"
    if is_asking_about_foodsliver_ai(user_message):
        predefined_response = (
            "Foods Liver AI is your personal assistant for everything related to food, "
            "nutrition, recipes, and meal planning. 🍎🥗 It provides detailed recipes, "
            "nutrition facts, cooking tips, and helps you make healthier food choices. "
            "Just ask anything about food, and Foods Liver AI is here to assist you! 😊"
        )
        return jsonify({"reply": predefined_response, "show_ad": False})

    # Initialize chat history if not present
    if "chat_history" not in session:
        session["chat_history"] = [{"role": "system", "content": "You are a helpful Food and Nutrition Expert AI."}]
        session["bot_response_count"] = 0

    session["chat_history"].append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}",
            headers={"Content-Type": "application/json", "api-key": AZURE_OPENAI_API_KEY},
            json={"messages": session["chat_history"], "max_tokens": 512, "temperature": 0.7}
        )
        response.raise_for_status()

        assistant_message = response.json()["choices"][0]["message"]["content"]
        cleaned_message = clean_response(assistant_message)

        session["chat_history"].append({"role": "assistant", "content": assistant_message})
        session["bot_response_count"] += 1
        session.modified = True

        # Show AdSense ad after every 3 bot responses
        show_ad = session["bot_response_count"] % 3 == 0

        return jsonify({"reply": cleaned_message, "show_ad": show_ad})

    except requests.exceptions.HTTPError as http_err:
        return jsonify({"error": f"HTTP error: {http_err}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

@app.route("/reset", methods=["POST"])
def reset_chat():
    """Reset chat history."""
    session.pop("chat_history", None)
    session.pop("bot_response_count", None)
    return jsonify({"message": "Chat history cleared. Start a new conversation!"})

if __name__ == "__main__":
    app.run(debug=True)
