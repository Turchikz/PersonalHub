import io
import json
import logging
import os
import urllib.error
import urllib.request
import wave

from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)
MAX_AUDIO_BYTES = 8 * 1024 * 1024


class PiperTTSError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.status_code = status_code


def _word(number, forms):
    if 11 <= number % 100 <= 14:
        return forms[2]
    if number % 10 == 1:
        return forms[0]
    if 2 <= number % 10 <= 4:
        return forms[1]
    return forms[2]


def get_countdown_text(event, now=None):
    remaining = (event.target_datetime - (now if now is not None else timezone.now())).total_seconds()
    title = f"Событие «{event.title}»"
    if remaining <= 0:
        return f"{title} наступило."
    if remaining < 60:
        return f"{title} наступит меньше чем через минуту."

    days, rest = divmod(int(remaining), 86400)
    hours, rest = divmod(rest, 3600)
    minutes = rest // 60
    parts = []
    for number, forms in (
        (days, ("день", "дня", "дней")),
        (hours, ("час", "часа", "часов")),
        (minutes, ("минуту", "минуты", "минут")),
    ):
        if number:
            parts.append(f"{number} {_word(number, forms)}")
    duration = parts[0] if len(parts) == 1 else f"{', '.join(parts[:-1])} и {parts[-1]}"
    return f"{title} наступит через {duration}."


def get_speech_audio(text):
    url = (
        getattr(settings, "PIPER_TTS_URL", None)
        or os.environ.get("PIPER_TTS_URL")
        or "http://127.0.0.1:5001/synthesize"
    )
    payload = json.dumps({"text": text}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8", "Accept": "audio/wav"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            if response.headers.get_content_type() != "audio/wav":
                raise PiperTTSError("Сервис озвучивания вернул неверный формат ответа.")
            audio = response.read(MAX_AUDIO_BYTES + 1)
    except urllib.error.HTTPError as error:
        logger.warning("Piper TTS returned HTTP %s", error.code)
        raise PiperTTSError("Сервис озвучивания не смог создать аудио.") from error
    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise PiperTTSError("Сервис озвучивания не ответил вовремя.", 504) from error
        logger.warning("Piper TTS is unavailable")
        raise PiperTTSError("Сервис озвучивания сейчас недоступен.", 503) from error
    except TimeoutError as error:
        raise PiperTTSError("Сервис озвучивания не ответил вовремя.", 504) from error
    except OSError as error:
        raise PiperTTSError("Не удалось получить аудио от сервиса озвучивания.") from error

    if len(audio) > MAX_AUDIO_BYTES:
        raise PiperTTSError("Сервис озвучивания вернул слишком большой файл.")
    try:
        with wave.open(io.BytesIO(audio), "rb") as wav_file:
            if wav_file.getnframes() == 0:
                raise PiperTTSError("Сервис озвучивания вернул пустое аудио.")
    except (wave.Error, EOFError) as error:
        raise PiperTTSError("Сервис озвучивания вернул повреждённое аудио.") from error
    return audio
