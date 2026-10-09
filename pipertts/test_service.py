import io
import json
import sys
import urllib.error
import urllib.request
import wave
from pathlib import Path


def main():
    base_url = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5001").rstrip("/")
    with urllib.request.urlopen(f"{base_url}/health", timeout=10) as response:
        health = json.load(response)
    if health.get("status") != "ok":
        raise RuntimeError(f"Unexpected health response: {health}")

    payload = json.dumps(
        {"text": "До отпуска осталось два дня, пять часов и десять минут."},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/synthesize", data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        if response.headers.get_content_type() != "audio/wav":
            raise RuntimeError("Service did not return audio/wav")
        audio = response.read()

    with wave.open(io.BytesIO(audio), "rb") as wav_file:
        if wav_file.getnframes() <= 0:
            raise RuntimeError("Service returned empty audio")
        duration = wav_file.getnframes() / wav_file.getframerate()

    output = Path("piper-test.wav")
    output.write_bytes(audio)
    print(f"OK: voice={health['voice']}, audio={duration:.1f}s, file={output.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except (urllib.error.URLError, RuntimeError, wave.Error) as error:
        print(f"Piper test failed: {error}", file=sys.stderr)
        raise SystemExit(1)
