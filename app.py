from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

from llm import evaluate_coaching, classify_reflection, simulate_athlete_response, score_reflection

# Firebase setup
import firebase_admin
from firebase_admin import credentials, firestore

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Firebase init
cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Reflection endpoint
@app.route("/reflect", methods=["POST"])
def reflect():
    data = request.get_json()
    message = data.get("message", "")
    sentiment = classify_reflection(message)
    score = score_reflection(message)
    return jsonify({"sentiment": sentiment, "score": score})

# Simulation endpoint
@app.route("/simulate", methods=["POST"])
def simulate():
    data = request.get_json()
    profile = data.get("profile", {})
    chat_history = data.get("chat_history", [])
    response = simulate_athlete_response(profile, chat_history)

    db.collection("simulations").add({
        "athlete_profile": profile,
        "chat_history": chat_history,
        "athlete_response": response,
        "timestamp": firestore.SERVER_TIMESTAMP,
    })

    return jsonify({"athlete_response": response})

# Mistral-based team message generation
@app.route('/team_message', methods=['POST'])
def team_message():
    data = request.get_json()
    avg_score = data.get("avgScore", 5)
    summary = data.get("summary", "")

    prompt = f"""
You're a team sports coach trying to motivate your athletes.

Team outlook: {summary}
Average mood score: {avg_score}

Write a short, encouraging message to the team:
"""

    res = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": prompt, "stream": False}
    )

    return jsonify({ "message": res.json()["response"].strip() })

@app.route("/evaluate", methods=["POST"])
def evaluate():
    data = request.get_json()
    profile = data.get("profile", {})
    chat_history = data.get("chat_history", [])
    result = evaluate_coaching(profile, chat_history)
    return jsonify({"evaluation": result})

@app.route("/delete_account", methods=["POST"])
def delete_account():
    data = request.get_json()
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Only allow deletion if user is an athlete
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({"success": False, "error": "User not found"}), 404

    if user_doc.to_dict().get("role") != "athlete":
        return jsonify({"success": False, "error": "Only athletes can delete their account"}), 403

    user_ref.delete()
    return jsonify({"success": True, "message": "Account deleted"})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
