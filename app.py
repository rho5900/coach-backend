from flask import Flask, request, jsonify
from flask_cors import CORS
from llm import evaluate_coaching 
from llm import classify_reflection, simulate_athlete_response


# Firebase setup
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)

# 💥 This is the magic line: sets wildcard CORS headers for *every* route
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Firebase init
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Reflection endpoint (Stage 1)
@app.route("/reflect", methods=["POST"])
def reflect():
    data = request.get_json()
    message = data.get("message", "")
    sentiment = classify_reflection(message)

    # Save to Firestore
    db.collection("reflections").add({
        "athlete": "AthleteA",  # Hardcoded for now
        "message": message,
        "sentiment": sentiment,
        "timestamp": firestore.SERVER_TIMESTAMP,
    })

    return jsonify({"sentiment": sentiment})

# Simulation endpoint (Stage 4)
@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()
    profile = data.get("profile", {})
    chat_history = data.get("chat_history", [])
    response = simulate_athlete_response(profile, chat_history)

    # Optional: Save simulated chat to Firestore
    db.collection("simulations").add({
        "athlete_profile": profile,
        "chat_history": chat_history,
        "athlete_response": response,
        "timestamp": firestore.SERVER_TIMESTAMP,
    })
    
    return jsonify({"athlete_response": response})

@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    profile = data.get("profile", {})
    chat_history = data.get("chat_history", [])
    result = evaluate_coaching(profile, chat_history)

    return jsonify({"evaluation": result})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
