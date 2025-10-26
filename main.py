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
# import pyttsx3
import tempfile
import re
import random_responses
# from googlesearch import search

# Local-only TTS (pyttsx3)
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


GTTS_VOICES = {
    "gtts_uk": {"lang": "en", "tld": "co.uk"},        # British
    "gtts_us": {"lang": "en", "tld": "com"},          # American
    "gtts_aus": {"lang": "en", "tld": "com.au"},      # Australian
    "gtts_ind": {"lang": "en", "tld": "co.in"},       # Indian English
}

def list_pyttsx3_voices():
    """Return available voice names and IDs for pyttsx3."""
    if not has_pyttsx3:
        return []
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    return [{"id": v.id, "name": v.name, "gender": getattr(v, "gender", "")} for v in voices]

def load_json(file):
    with open(file, "r", encoding="utf-8") as bot_responses:
        print(f"Loaded '{file}' successfully!")
        botly_responses = json.load(bot_responses)
        return botly_responses

response_data = load_json("bot.json")


def extract_user_name(input_string: str):
    # Regular expression to capture the user's name
    name_pattern = re.compile(r"(?i)(?:I\s+am\s+called|My\s+name\s+is)\s+([^\s.,;?!]+)")

    # Try to find a match in the input string
    match = name_pattern.search(input_string)
    
    if match:
        # Extract and return the user's name
        return match.group(1)

    return None


def calculate_response(input_string: str):
    split_message = re.split(r'\s+|[,;?!.-]\s*', input_string.lower())
    score_list = []
    
    user_name = extract_user_name(input_string)
    
    if user_name:
        # Return a response specifically for mentioning the user's name
        random_reponses = [
            f"Hey {user_name}! Nice to hear from you. I am Botly by the way",
            f"Wow, I like your name {user_name}! Did your grand mother give it to you?",
            f"It feels nice to know you {user_name}! How are you?",
            f"You have a nice name {user_name}! I wish we could shake hands but sadly, I am yet to have some",
            f"Great knowing you {user_name}! I am Botly by the way."
       
    ]
        list_count = len(random_reponses)
        random_item = random.randrange(list_count)

        return random_reponses[random_item]
        # return f"Hey {user_name}! Nice to hear from you."

    # Check all the responses
    for response in response_data:
        response_score = 0
        required_score = 0
        required_words = response["required_words"]

        # Check if there are any required words
        if required_words:
            for word in split_message:
                if word in required_words:
                    required_score += 1

        # Amount of required words should match the required score
        if required_score == len(required_words):
            # Check each word the user has typed
            for word in split_message:
                # If the word is in the response, add to the score
                if word in response["user_input"]:
                    response_score += 1

        # Add score to list
        score_list.append(response_score)

    # Find the best response and return it if they're not all 0
    best_response = max(score_list, default=0)
    if best_response != 0:

            
        response_index = score_list.index(best_response)
        possible_responses = response_data[response_index]["bot_response"]
        
        list_count = len(possible_responses)
        random_item = random.randrange(list_count)
        selected_response = possible_responses[random_item]
        # selected_response = random.choice(possible_responses)
        return selected_response
    

    return random_responses.random_string()


@app.get("/")
def root():
    return {
        "message": "Jarvis backend is alive!",
        "available_gtts_voices": list(GTTS_VOICES.keys()),
        "available_pyttsx3_voices": list_pyttsx3_voices()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("🎧 WebSocket connected!")

    try:
        while True:
            data = await websocket.receive_json()
            # text = await websocket.receive_text()
            msg_type = data.get("type")
            text = data.get("text", "")
            engine = data.get("engine", "gtts_uk")
            voice_id = data.get("voice_id") 

            if text == "__greet__":
                   greeting = random.choice([
                    "Hello there! It feels nice to talk to you again.",
                    "Hey! How’s your day going so far?",
                    "Ah, there you are! I was just thinking we should chat."
                   ])
            await websocket.send_text(greeting)
                

            if msg_type == "chat":
                print(f"User: {text}")
              

                response = calculate_response(text)
                # await websocket.send_text(f"🤖 Jarvis: I received '{text}'")
                await websocket.send_text(response)

                try:
                    audio_bytes = await synthesize_tts("gtts_uk", response, None)
                    if audio_bytes:
                       b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                       await websocket.send_json({
                             "type": "tts_result",
                             "engine": "gtts_uk",
                            "audio": b64_audio
                        })
                except Exception as e:
                  print("TTS failed:", e)
                await websocket.send_json({
                   "type": "error",
                   "message": "TTS failed on server."
               })
                continue
                
                
                
            # talk(response)
            # return { "bot": response}

            elif msg_type == "tts":
                print(f"TTS requested ({engine}): {text}")
                audio_bytes = await synthesize_tts(engine, text, voice_id)
                if audio_bytes:
                    b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                    await websocket.send_json({
                        "type": "tts_result",
                        "engine": engine,
                        "audio": b64_audio
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"TTS engine '{engine}' unavailable."
                    })

    except WebSocketDisconnect:
        print("❌ Client disconnected.")

async def synthesize_tts(engine: str, text: str, voice_id: str | None = None) -> bytes:
    """Generate speech bytes using gTTS or pyttsx3."""
    if not text.strip():
        return b""

    # ============= gTTS OPTIONS =============
    if engine.startswith("gtts"):
        config = GTTS_VOICES.get(engine, GTTS_VOICES["gtts_uk"])
        tts = gTTS(text=text, lang=config["lang"], tld=config["tld"])
        buf = BytesIO()
        tts.write_to_fp(buf)
        return buf.getvalue()

    # ============= pyttsx3 LOCAL =============
    elif engine == "pyttsx3" and has_pyttsx3:
        tts_engine = pyttsx3.init()
        voices = tts_engine.getProperty("voices")

        # Try setting selected voice ID
        if voice_id:
            try:
                tts_engine.setProperty("voice", voice_id)
            except Exception as e:
                print(f"⚠️ Invalid voice_id {voice_id}: {e}")
        else:
            # Try female fallback
            for voice in voices:
                if "female" in voice.name.lower() or "zira" in voice.name.lower() or "hazel" in voice.name.lower():
                    tts_engine.setProperty("voice", voice.id)
                    break

        tmp_path = "temp_tts.wav"
        tts_engine.save_to_file(text, tmp_path)
        tts_engine.runAndWait()

        with open(tmp_path, "rb") as f:
            audio_data = f.read()
        os.remove(tmp_path)
        return audio_data

    return b""



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)



