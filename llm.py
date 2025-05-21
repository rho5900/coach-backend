import requests

def classify_reflection(message):
    prompt = f"""
You are a wellness assistant. Classify this athlete's post-game reflection as:
- 'Positive'
- 'Neutral'
- 'Red Flag' (if signs of frustration, sadness, burnout, or distress).

Message: {message}
Your classification (just one word):
"""

    res = requests.post("http://localhost:11434/api/generate", json={
        "model": "mistral",
        "prompt": prompt,
        "stream": False
    })

    return res.json()["response"].strip()

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

    res = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": prompt, "stream": False}
    )
    return res.json()["response"].strip()


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

    res = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "mistral", "prompt": prompt, "stream": False}
    )

    result = res.json()["response"].strip()

    # Log it so you can debug it during dev
    print("\n🧠 Mistral Evaluation Output:\n", result)

    return result