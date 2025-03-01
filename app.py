from flask import Flask, request, jsonify, render_template, session
from flask_session import Session  # Flask-Session for session storage
import os
import requests
from dotenv import load_dotenv
import re
import tempfile  # To store session files in a temp directory
from flask_cors import CORS  # Import CORS from flask_cors

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Set Flask Secret Key (Ensure this is set in Azure App Service)
app.secret_key = os.getenv("FLASK_SECRET_KEY")



# Enable CORS with support for credentials (important for embedded iframes)
CORS(app, supports_credentials=True)

@app.after_request
def set_cookies(response):
    response.headers["Access-Control-Allow-Origin"] = "*"  # Allow all origins
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.set_cookie(
        "session",
        httponly=True,
        secure=True,  # Set this to False for local testing
        samesite="None"  # Important for embedded iframes
    )
    return response

# Azure OpenAI API Configuration (Ensure these are set in Azure's environment variables)
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
                "are tailored to the needs and preferences of the user.\n\n"
                "# Guidelines:\n"
                "- **Expertise**: Provide precise measurements, techniques, and substitutions where applicable.\n"
                "- **Cultural Awareness**: Be mindful of global culinary traditions (vegan, halal, kosher, etc.).\n"
                "- **Clarity and Precision**: Use clear step-by-step instructions.\n"
                "- **Customizability**: Tailor suggestions to user preferences, skill level, and available ingredients.\n\n"
                "# Output Format:\n"
                "For recipes: \n"
                "- Title\n"
                "- Ingredients (with quantities)\n"
                "- Instructions (step-by-step)\n"
                "- Serving Suggestions\n"
                "- Nutrition Information (optional)\n\n"
                "For nutrition advice: Provide concise and clear responses."
            )
        }]
        session["bot_response_count"] = 0

    # Handle "continue" functionality
    if user_message.lower() == "continue" and len(session["chat_history"]) > 1:
        user_message = f"Continue from where you left off: {session['chat_history'][-1]['content']}"

    session["chat_history"].append({"role": "user", "content": user_message})
    session.modified = True  # Ensure session changes are saved

    try:
        response = requests.post(
            f"{AZURE_OPENAI_ENDPOINT}/openai/deployments/{AZURE_OPENAI_DEPLOYMENT_NAME}/chat/completions?api-version={AZURE_OPENAI_API_VERSION}",
            headers={"Content-Type": "application/json", "api-key": AZURE_OPENAI_API_KEY},
            json={"messages": session["chat_history"], "max_tokens": 512, "temperature": 0.6}
        )
        response.raise_for_status()

        assistant_message = response.json()["choices"][0]["message"]["content"]
        cleaned_message = clean_response(assistant_message)

        # Save assistant response in session
        session["chat_history"].append({"role": "assistant", "content": assistant_message})
        session["bot_response_count"] += 1
        session.modified = True  # Ensure session changes are saved

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
    app.run(host="0.0.0.0", port=5000, debug=True)
