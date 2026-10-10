from django.db.models import Prefetch
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .models import CheckResult, Monitor, MonitorNotification


def dashboard_context():
    monitors = list(Monitor.objects.prefetch_related(Prefetch(
        "checks", queryset=CheckResult.objects.order_by("-checked_at", "-pk")[:10],
        to_attr="recent_checks",
    )))
    notifications = list(MonitorNotification.objects.select_related("monitor")[:10])
    return {
        "monitors": monitors, "monitor_notifications": notifications,
        "monitor_latest_notification_id": notifications[0].pk if notifications else 0,
    }


@never_cache
@require_GET
def status(request):
    context = dashboard_context()
    return JsonResponse({
        "html": render_to_string("monitoring/panel.html", context, request=request),
        "notifications": [{"id": item.pk, "message": item.message}
                          for item in context["monitor_notifications"]],
    })
