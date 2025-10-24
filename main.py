# pip install fastapi uvicorn python-multipart
# python main.py

# http://localhost:5000/


# backend/main.py
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os

app = FastAPI()

# Allow frontend to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Jarvis backend is alive!"}

# Example voice upload route (will be used later for speech-to-text)
@app.post("/voice")
async def receive_audio(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Dummy response for now (replace with Whisper later)
    response_text = "I received your audio successfully!"

    # Clean up
    os.remove(tmp_path)
    return {"transcript": response_text}


# Run locally
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
