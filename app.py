from fastapi import FastAPI, Request
from pydub import AudioSegment
import base64
import tempfile
import os

app = FastAPI()

@app.post("/split-audio")
async def split_audio(request: Request):
    data = await request.json()
    audio_b64 = data["audio_base64"]
    mime_type = data.get("mime_type", "audio/mpeg")
    extension = mime_type.split("/")[-1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as f:
        f.write(base64.b64decode(audio_b64))
        audio_path = f.name

    audio = AudioSegment.from_file(audio_path)
    duration_ms = len(audio)
    max_size = 25 * 1024 * 1024
    step_ms = 60 * 1000
    start = 0
    chunks = []

    while start < duration_ms:
        end = min(start + step_ms, duration_ms)
        chunk = audio[start:end]

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as cf:
            chunk.export(cf.name, format=extension)
            if os.path.getsize(cf.name) > max_size:
                step_ms = int(step_ms * 0.8)
                continue

            with open(cf.name, "rb") as r:
                chunk_b64 = base64.b64encode(r.read()).decode("utf-8")
                chunks.append({
                    "chunk_base64": chunk_b64,
                    "start_ms": start,
                    "end_ms": end
                })

            start = end

    return {"status": "ok", "chunks": chunks}
