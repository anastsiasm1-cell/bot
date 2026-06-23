"""
Локальный сервис распознавания речи на базе faster-whisper.
Принимает аудио/видео файл и возвращает распознанный текст.
"""
import asyncio
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small")
COMPUTE_TYPE = os.environ.get("WHISPER_COMPUTE_TYPE", "int8")
LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "ru")
BEAM_SIZE = int(os.environ.get("WHISPER_BEAM_SIZE", "5"))

app = FastAPI(title="Local Speech-to-Text Service")

model = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)


def _run_transcription(path: str) -> str:
    segments, _info = model.transcribe(
        path, language=LANGUAGE, vad_filter=True, beam_size=BEAM_SIZE
    )
    return "".join(segment.text for segment in segments).strip()


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL_SIZE}


@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename or "")[1] or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        text = await asyncio.to_thread(_run_transcription, tmp_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        os.unlink(tmp_path)

    return {"text": text}
