import asyncio
import base64
import os
from io import BytesIO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from dotenv import load_dotenv
import json
import random
import re
import requests
import tempfile

# Local TTS fallback
try:
    import pyttsx3
    has_pyttsx3 = True
except ImportError:
    has_pyttsx3 = False

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== CONFIG =====================

LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"
# LMSTUDIO_MODEL = "mistral-7b-instruct-v0.2" Best
LMSTUDIO_MODEL ="tinyllama-1.1b-chat-v1.0"
# LMSTUDIO_MODEL = "phi-3-mini"  


GTTS_VOICES = {
    "gtts_uk": {"lang": "en", "tld": "co.uk"},
    "gtts_us": {"lang": "en", "tld": "com"},
    "gtts_aus": {"lang": "en", "tld": "com.au"},
    "gtts_ind": {"lang": "en", "tld": "co.in"},
}

# ===================== HELPERS =====================

def list_pyttsx3_voices():
    if not has_pyttsx3:
        return []
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    return [{"id": v.id, "name": v.name} for v in voices]


def load_json(file):
    try:
        with open(file, "r", encoding="utf-8") as f:
            print(f"Loaded '{file}' successfully!")
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load {file}: {e}")
        return []


response_data = load_json("bot.json")

def load_custom_knowledge(file="custom_knowledge.json"):
    try:
        with open(file, "r", encoding="utf-8") as f:
            print(f"Loaded '{file}' successfully!")
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Could not load {file}: {e}")
        return []

custom_knowledge = load_custom_knowledge()


def extract_user_name(input_string: str):
    pattern = re.compile(r"(?i)(?:I\s+am\s+called|My\s+name\s+is)\s+([^\s.,;?!]+)")
    match = pattern.search(input_string)
    return match.group(1) if match else None


def check_custom_knowledge(user_input: str):
    for entry in custom_knowledge:
        if any(keyword.lower() in user_input.lower() for keyword in entry.get("keywords", [])):
            return random.choice(entry["responses"])
    return None


# ===================== OLLAMA INTEGRATION =====================

def query_local_ai(prompt: str) -> str:
    """Query LM Studio for intelligent, conversational responses."""
    try:
#         system_prompt = (
#     "You are Jarvis, Tony Stark's personal AI assistant. "
#     "Speak confidently, politely, and directly. "
#     "Keep replies short and conversational. "
#     "Do NOT mention being an AI or who created you. "
#     "Always sound like Jarvis from Iron Man — calm, formal, and efficient."
# )       
        payload = {
    "model": LMSTUDIO_MODEL,
    "messages": [
        # {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
        
    ],

    "max_tokens": 256,
    "temperature": 0.7
}
    # "messages": [
    #     {"role": "system", "content": system_prompt},
    #     {"role": "user", "content": prompt}
    # ],


        response = requests.post(LMSTUDIO_URL, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            return data["choices"][0]["message"]["content"].strip()
        else:
            return "I'm thinking, but something feels off with my circuits."

    except Exception as e:
        print("⚠️ LM Studio AI error:", e)
        return "Sorry, I couldn’t connect to my local mind system. Try again."



# ===================== MAIN CHAT LOGIC =====================

# def calculate_response(user_input: str):
#     """
#     Send user input directly to LM Studio model for natural Jarvis-style chat.
#     """
#     if not user_input.strip():
#         return "I'm here. Go ahead."

#     print("🤖 Querying LM Studio...")
#     return query_local_ai(user_input)


def calculate_response(user_input: str):
    user_name = extract_user_name(user_input)
    if user_name:
        responses = [
            f"Hey {user_name}! Nice to hear from you. I’m Botly, your AI companion.",
            f"I like your name, {user_name}! Did your grandma give it to you?",
            f"It’s great to meet you, {user_name}! How are you feeling today?"
        ]
        return random.choice(responses)

    knowledge_reply = check_custom_knowledge(user_input)
    if knowledge_reply:
        return knowledge_reply

    # split_message = re.split(r'\s+|[,;?!.-]\s*', user_input.lower())
    # score_list = []

    # for response in response_data:
    #     score = 0
    #     required_words = response.get("required_words", [])
    #     if all(word in split_message for word in required_words):
    #         for word in split_message:
    #             if word in response.get("user_input", []):
    #                 score += 1
    #     score_list.append(score)

    # best_response = max(score_list, default=0)
    # if best_response != 0:
    #     idx = score_list.index(best_response)
    #     possible = response_data[idx]["bot_response"]
    #     return random.choice(possible)

    # Fallback to local AI (intelligent response)
    # print("🤖 Falling back to Ollama intelligent response...")
    return query_local_ai(user_input)


# ===================== ROUTES =====================

@app.get("/")
def root():
    return {
        "message": "Jarvis backend is alive and connected to local AI!",
        "available_gtts_voices": list(GTTS_VOICES.keys()),
        "available_pyttsx3_voices": list_pyttsx3_voices(),
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🎧 WebSocket connected!")

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            text = data.get("text", "")
            engine = data.get("engine", "gtts_uk")
            voice_id = data.get("voice_id")

            if text == "__greet__":
                greeting = random.choice([
                    "Hello there! Feels nice to talk to you again.",
                    "Hey! How’s your day going so far?",
                    "Ah, there you are! I was just thinking we should chat."
                ])
                await websocket.send_text(greeting)
                continue

            if msg_type == "chat":
                print(f"User: {text}")
                response = calculate_response(text)
                await websocket.send_text(response)

                try:
                    audio_bytes = await synthesize_tts(engine, response, voice_id)
                    if audio_bytes:
                        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                        await websocket.send_json({
                            "type": "tts_result",
                            "engine": engine,
                            "audio": b64_audio,
                        })
                except Exception as e:
                    print("TTS failed:", e)
                continue

            elif msg_type == "tts":
                print(f"TTS requested ({engine}): {text}")
                audio_bytes = await synthesize_tts(engine, text, voice_id)
                if audio_bytes:
                    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    await websocket.send_json({
                        "type": "tts_result",
                        "engine": engine,
                        "audio": b64_audio,
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"TTS engine '{engine}' unavailable.",
                    })

    except WebSocketDisconnect:
        print("❌ Client disconnected.")


# ===================== TTS =====================

async def synthesize_tts(engine: str, text: str, voice_id: str | None = None) -> bytes:
    if not text.strip():
        return b""

    if engine.startswith("gtts"):
        config = GTTS_VOICES.get(engine, GTTS_VOICES["gtts_uk"])
        tts = gTTS(text=text, lang=config["lang"], tld=config["tld"])
        buf = BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()

    elif engine == "pyttsx3" and has_pyttsx3:
        tts_engine = pyttsx3.init()
        voices = tts_engine.getProperty("voices")
        if voice_id:
            tts_engine.setProperty("voice", voice_id)
        tmp = "temp_tts.wav"
        tts_engine.save_to_file(text, tmp)
        tts_engine.runAndWait()
        with open(tmp, "rb") as f:
            data = f.read()
        os.remove(tmp)
        return data

    return b""


# ===================== ENTRY =====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)


