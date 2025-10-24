import asyncio
import base64
import os
from io import BytesIO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from gtts import gTTS
from dotenv import load_dotenv

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
            msg_type = data.get("type")
            text = data.get("text", "")
            engine = data.get("engine", "gtts_uk")
            voice_id = data.get("voice_id") 

            if msg_type == "chat":
                print(f"User: {text}")
                await websocket.send_text(f"🤖 Jarvis: I received '{text}'")

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


# ======================================================
#  MAIN
# ======================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)



# import asyncio
# import base64
# import os
# from io import BytesIO
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# from gtts import gTTS
# from dotenv import load_dotenv

# # Local-only TTS (pyttsx3)
# try:
#     import pyttsx3
#     has_pyttsx3 = True
# except ImportError:
#     has_pyttsx3 = False

# load_dotenv()

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# @app.get("/")
# def root():
#     return {"message": "Jarvis backend is alive!"}


# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     print("🎧 WebSocket connected!")

#     try:
#         while True:
#             data = await websocket.receive_json()
#             msg_type = data.get("type")
#             text = data.get("text", "")
#             engine = data.get("engine", "gtts")

#             if msg_type == "chat":
#                 print(f"User: {text}")
#                 await websocket.send_text(f"🤖 Jarvis: I received '{text}'")

#             elif msg_type == "tts":
#                 print(f"TTS requested ({engine}): {text}")
#                 audio_bytes = await synthesize_tts(engine, text)
#                 if audio_bytes:
#                     b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
#                     await websocket.send_json({
#                         "type": "tts_result",
#                         "engine": engine,
#                         "audio": b64_audio
#                     })
#                 else:
#                     await websocket.send_json({
#                         "type": "error",
#                         "message": f"TTS engine '{engine}' unavailable."
#                     })

#     except WebSocketDisconnect:
#         print("❌ Client disconnected.")


# async def synthesize_tts(engine: str, text: str) -> bytes:
#     """Generate speech bytes using gTTS or pyttsx3."""
#     if not text.strip():
#         return b""

#     # ============= gTTS =============
#     if engine == "gtts":
#         tts = gTTS(text=text, lang="en", tld="co.uk")
#         buf = BytesIO()
#         tts.write_to_fp(buf)
#         return buf.getvalue()

#     # ============= pyttsx3 (local only) =============
#     elif engine == "pyttsx3" and has_pyttsx3:
#         tts_engine = pyttsx3.init()
#         voices = tts_engine.getProperty("voices")
#         # Pick female voice if available
#         for voice in voices:
#             if "female" in voice.name.lower() or "woman" in voice.name.lower():
#                 tts_engine.setProperty("voice", voice.id)
#                 break

#         tmp_path = "temp_tts.wav"
#         tts_engine.save_to_file(text, tmp_path)
#         tts_engine.runAndWait()

#         with open(tmp_path, "rb") as f:
#             audio_data = f.read()
#         os.remove(tmp_path)
#         return audio_data

#     return b""


# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)



# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# import uvicorn
# from gtts import gTTS
# import io, base64

# app = FastAPI()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.get("/")
# def root():
#     return {"message": "Jarvis backend is alive!"}

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             # Receive message from client
#             data = await websocket.receive_text()
#             print(f"Client says: {data}")

#             # Respond back (you’ll replace this with your AI logic later)
#             await websocket.send_text(f"🤖 Jarvis: I received '{data}'")
#     except WebSocketDisconnect:
#         print("Client disconnected")

# @app.websocket("/ws/voice")
# async def voice_ws(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             text = await websocket.receive_text()
#             print(f"User said: {text}")

#             # Generate female TTS
#             tts = gTTS(text=f"I heard you say: {text}", lang="en", tld="co.uk")
#             buffer = io.BytesIO()
#             tts.write_to_fp(buffer)
#             audio_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

#             # Send audio as Base64 string
#             await websocket.send_json({"audio": audio_base64})
#     except WebSocketDisconnect:
#         print("Voice client disconnected")


# @app.websocket("/ws/chat")
# async def chat_ws(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             text = await websocket.receive_text()
#             print(f"Chat: {text}")
#             await websocket.send_text(f"AI: I heard '{text}'")
#     except WebSocketDisconnect:
#         print("Chat client disconnected")


# @app.websocket("/ws/audio")
# async def audio_ws(websocket: WebSocket):
#     await websocket.accept()
#     try:
#         while True:
#             audio_bytes = await websocket.receive_bytes()
#             print(f"Received {len(audio_bytes)} bytes of audio data.")
#             # Later: transcribe and reply with text or TTS
#     except WebSocketDisconnect:
#         print("Audio stream ended.")


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)

