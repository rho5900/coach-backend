import requests
import re
import os

TOGETHER_API_KEY = os.environ.get("TOGETHER_API_KEY")
TOGETHER_URL = "https://api.together.xyz/inference"
MODEL_NAME = "Qwen/Qwen2.5-7B-Instruct-Turbo"


def extract_text(data, default="Neutral"):
    output = data.get("output")
    if isinstance(output, str):
        return output.strip()
    if isinstance(output, dict):
        return output.get("choices", [{}])[0].get("text", default).strip()
    if "choices" in data:
        return data["choices"][0].get("text", default).strip()
    print("⚠️ Unexpected LLM output:", data)
    return default


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
    return extract_text(res.json(), default="Neutral")


def simulate_athlete_response(profile, chat_history):
    def format_chat(chat_history):
        return "\n".join(
            f"Coach: {msg['message']}" if msg['sender'] == 'coach' else f"Athlete: {msg['message']}"
            for msg in chat_history
            if msg['sender'] in ('coach', 'athlete')
        )

    prompt = f"""
You are a high school athlete. Respond to your coach naturally in 1-2 sentences.

Your profile:
- Age: {profile.get('age', 'N/A')}
- Sport: {profile.get('sport', 'N/A')}
- Anxiety Level: {profile.get('anxiety_level', 'N/A')}
- Motivation Level: {profile.get('motivation_level', 'N/A')}
- Context: {profile.get('context', 'N/A')}

Conversation so far:
{format_chat(chat_history)}

IMPORTANT: Respond ONLY as the athlete. Do NOT include any instructions, explanations, or meta-text. Just give a natural response as if you're the athlete talking to your coach.
"""

    res = requests.post(
        TOGETHER_URL,
        headers={"Authorization": f"Bearer {TOGETHER_API_KEY}"},
        json={"model": MODEL_NAME, "prompt": prompt, "max_tokens": 100}
    )
    raw_response = extract_text(res.json(), default="I'm doing okay, Coach.")
    
    # Clean up the response - remove any prompt instructions or extra text
    athlete_reply = raw_response.strip()
    
    # Remove common AI instruction artifacts
    athlete_reply = athlete_reply.replace("You are an AI assistant", "").replace("You are simulating", "")
    athlete_reply = athlete_reply.replace("Remember to stay true to", "").replace("Athlete:", "")
    athlete_reply = athlete_reply.replace("Coach:", "").replace("Respond as the athlete", "")
    
    # Take only the first sentence or two
    sentences = athlete_reply.split('.')
    if len(sentences) > 2:
        athlete_reply = '. '.join(sentences[:2]) + '.'
    
    # Fallback if response is too short or contains instructions
    if len(athlete_reply) < 10 or "AI" in athlete_reply or "assistant" in athlete_reply.lower():
        athlete_reply = "I'm doing okay, Coach. Thanks for asking."
    
    return athlete_reply.strip()


def evaluate_coaching(profile, chat_history):
    def format_chat(chat_history):
        lines = [f"{msg['sender'].capitalize()}: {msg['message']}" for msg in chat_history]
        
        last_speaker = chat_history[-1]["sender"].lower()
        next_speaker = "athlete" if last_speaker == "coach" else "coach"
        
        lines.append(f"{next_speaker.capitalize()}:")  # <-- this is the key cue

        return "\n".join(lines)


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
    return extract_text(res.json(), default="Score: 7\nFeedback: Keep improving communication.")


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

    try:
        data = res.json()
        raw = extract_text(data, default="5")
        match = re.search(r'\b([1-9]|10)\b', raw)
        return int(match.group(1)) if match else 5
    except Exception as e:
        print("❌ Failed to parse score response:", e)
        return 5
