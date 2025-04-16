from fastapi import FastAPI, Query
import requests

app = FastAPI()
MODEL = "gemma3:latest"

# Ollama 서버 주소 (기본적으로 localhost:11434)
OLLAMA_SERVER = "http://localhost:11434"

@app.get("/chat")
def chat_get(prompt: str = Query("just say hi")):
    response = requests.post(
        f"{OLLAMA_SERVER}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=10  # Set the timeout value in seconds
    )
    return response.json()
