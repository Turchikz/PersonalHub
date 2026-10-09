import os
import re
import subprocess
import sys
from pathlib import Path


def main():
    voice = os.environ.get("PIPER_VOICE", "ru_RU-denis-medium")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", voice):
        raise ValueError("PIPER_VOICE must be a voice identifier")

    models_dir = Path(os.environ.get("PIPER_MODELS_DIR", "/models"))
    models_dir.mkdir(parents=True, exist_ok=True)
    model = models_dir / f"{voice}.onnx"
    config = models_dir / f"{voice}.onnx.json"

    if not model.is_file() or not config.is_file():
        print(f"Downloading voice: {voice}", flush=True)
        subprocess.run(
            [sys.executable, "-m", "piper.download_voices", "--data-dir", str(models_dir), voice],
            check=True,
        )

    print(f"Starting Piper TTS with voice: {voice}", flush=True)
    os.execvp(
        "gunicorn",
        [
            "gunicorn", "--bind", "0.0.0.0:5000",
            "--workers", "1", "--threads", "2",
            "--timeout", "120", "--access-logfile", "-",
            "--error-logfile", "-", "app:app",
        ],
    )


if __name__ == "__main__":
    main()
