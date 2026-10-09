import io
import os
import threading
import wave
from pathlib import Path

from flask import Flask, Response, jsonify, request
from piper import PiperVoice


VOICE_NAME = os.environ.get("PIPER_VOICE", "ru_RU-denis-medium")
MODELS_DIR = Path(os.environ.get("PIPER_MODELS_DIR", "/models"))
voice = PiperVoice.load(str(MODELS_DIR / f"{VOICE_NAME}.onnx"))
synthesis_lock = threading.Lock()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024


@app.get("/health")
def health():
    return jsonify(status="ok", voice=VOICE_NAME)


@app.post("/synthesize")
def synthesize():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("text"), str):
        return jsonify(error="Передайте JSON с текстовым полем text."), 400

    text = data["text"].strip()
    if not text or not any(char.isalnum() for char in text):
        return jsonify(error="Текст должен содержать буквы или цифры."), 400
    if len(text) > 500:
        return jsonify(error="Максимальная длина текста — 500 символов."), 400

    try:
        with synthesis_lock:
            with io.BytesIO() as buffer:
                with wave.open(buffer, "wb") as wav_file:
                    voice.synthesize_wav(text, wav_file)
                audio = buffer.getvalue()
    except Exception:
        app.logger.exception("Piper synthesis failed")
        return jsonify(error="Не удалось создать аудио."), 500

    return Response(audio, mimetype="audio/wav", headers={"Cache-Control": "no-store"})
