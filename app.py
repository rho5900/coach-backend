from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

from llm import evaluate_coaching, classify_reflection, simulate_athlete_response, simulate_coach_response, score_reflection

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
    
    # Determine who should respond next based on the last message sender
    if not chat_history:
        # If no chat history, start with athlete response
        response = simulate_athlete_response(profile, chat_history)
        return jsonify({"athlete_response": response})
    
    last_sender = chat_history[-1].get("sender", "").lower()
    
    if last_sender == "coach":
        # Coach just spoke, athlete should respond
        response = simulate_athlete_response(profile, chat_history)
        return jsonify({"athlete_response": response})
    elif last_sender == "athlete":
        # Athlete just spoke, coach should respond
        response = simulate_coach_response(profile, chat_history)
        return jsonify({"coach_response": response})
    else:
        # Fallback to athlete response
        response = simulate_athlete_response(profile, chat_history)
        return jsonify({"athlete_response": response})



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

    # Allow deletion for both athletes and coaches
    user_ref = db.collection("users").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({"success": False, "error": "User not found"}), 404

    user_data = user_doc.to_dict()
    user_role = user_data.get("role")
    
    if user_role not in ["athlete", "coach"]:
        return jsonify({"success": False, "error": "Only athletes and coaches can delete their account"}), 403

    # Delete the user document from Firestore
    user_ref.delete()
    
    # Optionally, you could also delete related data here
    # For example, delete athlete's reflections or coach's evaluations
    if user_role == "athlete":
        # Delete athlete's reflections
        reflections = db.collection("reflections").where("user_id", "==", user_id).stream()
        for reflection in reflections:
            reflection.reference.delete()
    elif user_role == "coach":
        # Delete coach's evaluations
        evaluations = db.collection("evaluations").where("coach_id", "==", user_id).stream()
        for evaluation in evaluations:
            evaluation.reference.delete()

    return jsonify({"success": True, "message": f"{user_role.capitalize()} account deleted successfully"})
    
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
