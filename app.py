from flask import Flask, request, jsonify, render_template, session
from flask_session import Session
import os
import requests
from dotenv import load_dotenv
import re
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Set Flask Secret Key (Ensure this is set in Azure)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Configure Flask-Session for File-Based Storage
SESSION_DIR = tempfile.gettempdir()

app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = SESSION_DIR
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True

# Initialize Flask-Session
Session(app)

# Azure OpenAI API Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")


def clean_response(text):
    """Cleans response from AI by removing unnecessary characters."""
    text = re.sub(r'[#*_~`]', '', text)  # Remove markdown characters
    text = re.sub(r'\n\s*\n', '<br><br>', text)  # Convert new lines to HTML line breaks
    return text.strip()


@app.route("/")
def index():
    """Render the chat UI."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """Handles user messages and returns AI responses."""
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Please enter a message."}), 400

    if "chat_history" not in session:
        session["chat_history"] = [{
            "role": "system",
            "content": (
                "You are Ottoman AI, a professional AI chef providing expert food and nutrition advice. "
                "Offer detailed, accurate, and culturally sensitive culinary information, ensuring your responses "
                "are tailored to the needs and preferences of the user."
            )
        }]
        session["bot_response_count"] = 0

    if user_message.lower() == "continue" and len(session["chat_history"]) > 1:
        user_message = f"Continue from where you left off: {session['chat_history'][-1]['content']}"

    session["chat_history"].append({"role": "user", "content": user_message})
    session.modified = True  

    try:
        response = requests.post(
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}",
            headers={"Content-Type": "application/json", "api-key": AZURE_OPENAI_API_KEY},
            json={"messages": session["chat_history"], "max_tokens": 512, "temperature": 0.6}
        )
        response.raise_for_status()

        assistant_message = response.json()["choices"][0]["message"]["content"]
        cleaned_message = clean_response(assistant_message)

        session["chat_history"].append({"role": "assistant", "content": assistant_message})
        session["bot_response_count"] += 1
        session.modified = True  

        return jsonify({"reply": cleaned_message})

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


@app.route("/reset", methods=["POST"])
def reset_chat():
    """Resets the chat session."""
    session.clear()
    return jsonify({"message": "Chat history has been reset."})


@app.route("/session_test")
def session_test():
    """Test route to check if sessions persist on Azure."""
    session["test"] = session.get("test", 0) + 1
    return f"Session count: {session['test']}"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
