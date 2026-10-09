from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from dashboard.models import CountdownEvent
from dashboard.services import PiperTTSError, get_countdown_text, get_speech_audio


def home(request):
    events = CountdownEvent.objects.order_by("target_datetime")
    return render(request, "dashboard/home.html", context={"events": events})


@require_POST
def event_speak(request, event_id):
    event = get_object_or_404(CountdownEvent, pk=event_id)
    try:
        audio = get_speech_audio(get_countdown_text(event))
    except PiperTTSError as error:
        return JsonResponse({"error": str(error)}, status=error.status_code)

    response = HttpResponse(audio, content_type="audio/wav")
    response["Cache-Control"] = "no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response
