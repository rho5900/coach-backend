# llm.py using Together.ai API (Fully Render-Compatible)

import requests
import re
import os

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_URL = "https://api.together.xyz/inference"
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"


def classify_reflection(message):
    prompt = f"""
You are a wellness assistant. Classify this athlete's post-game reflection as:
- 'Positive'
- 'Neutral'
- 'Red Flag' (if signs of frustration, sadness, burnout, or distress).

Message: {message}
Your classification (just one word):
"""
    res = requests.post(TOGETHER_URL,
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json={"model": MODEL_NAME, "prompt": prompt, "max_tokens": 20}
    )
    return res.json().get("output", "Neutral").strip()


def simulate_athlete_response(profile, chat_history):
    def format_chat(chat_history):
        return "\n".join(f"{msg['sender'].capitalize()}: {msg['message']}" for msg in chat_history)

    prompt = f"""
You are simulating a high school athlete chatting with their coach.

Athlete Profile:
- Age: {profile.get('age', 'N/A')}
- Sport: {profile.get('sport', 'N/A')}
- Anxiety Level: {profile.get('anxiety_level', 'N/A')}
- Motivation Level: {profile.get('motivation_level', 'N/A')}
- Context: {profile.get('context', 'N/A')}

Chat History:
{format_chat(chat_history)}

Respond as the athlete in 1–2 sentences. Be emotionally realistic and based on the profile above.
Athlete:
"""
    res = requests.post(TOGETHER_URL,
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json={"model": MODEL_NAME, "prompt": prompt, "max_tokens": 60}
    )
    return res.json().get("output", "Sure.").strip()


def evaluate_coaching(profile, chat_history):
    def format_chat(chat_history):
        return "\n".join(f"{msg['sender'].capitalize()}: {msg['message']}" for msg in chat_history)

    prompt = f"""
You are a coaching evaluator AI. Your job is to evaluate how well the coach supported the athlete in a conversation.

Athlete Profile:
- Age: {profile['age']}
- Sport: {profile['sport']}
- Anxiety Level: {profile['anxiety_level']}
- Motivation Level: {profile['motivation_level']}
- Context: {profile['context']}

Chat History:
{format_chat(chat_history)}

Respond ONLY in the following format:
Score: <number between 1 and 10>
Feedback: <one sentence of constructive feedback>
"""
    res = requests.post(TOGETHER_URL,
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json={"model": MODEL_NAME, "prompt": prompt, "max_tokens": 80}
    )
    return res.json().get("output", "Score: 7\nFeedback: Keep improving communication.").strip()


def score_reflection(message):
    prompt = f"""
You're an AI reflection evaluator. Rate the athlete's reflection strictly on a scale from 1 to 10.

Scale:
- 10: Very positive, detailed, motivated
- 5: Neutral, vague, or emotionally flat
- 1: Negative, unmotivated, or emotionally concerning

Only return the score as a number. Example:
7

Reflection:
{message}
Score:
"""
    res = requests.post(TOGETHER_URL,
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json={"model": MODEL_NAME, "prompt": prompt, "max_tokens": 10}
    )
    raw = res.json().get("output", "5").strip()
    match = re.search(r'\b([1-9]|10)\b', raw)
    return int(match.group(1)) if match else 5