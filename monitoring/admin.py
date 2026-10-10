from django.contrib import admin
from django.db import transaction
from django.utils import timezone

from .models import CheckResult, Monitor, MonitorNotification, MonitorState


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "is_active", "interval_minutes", "state", "last_checked_at")
    list_filter = ("is_active", "state")
    search_fields = ("name", "url")
    readonly_fields = ("state", "last_checked_at", "next_check_at", "created_at")

    def save_model(self, request, obj, form, change):
        # Apply settings immediately; the worker will establish a fresh baseline.
        with transaction.atomic():
            if change:
                current = Monitor.objects.select_for_update().get(pk=obj.pk)
                obj.state = current.state
                obj.last_checked_at = current.last_checked_at
                if {"url", "control_url"}.intersection(form.changed_data):
                    obj.state = MonitorState.UNKNOWN
                    obj.last_checked_at = None
            obj.next_check_at = timezone.now()
            super().save_model(request, obj, form, change)


class HistoryAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(CheckResult)
class CheckResultAdmin(HistoryAdmin):
    list_display = ("monitor", "checked_at", "state", "status_code", "response_time_ms")
    list_filter = ("state", "monitor")


@admin.register(MonitorNotification)
class MonitorNotificationAdmin(HistoryAdmin):
    list_display = ("monitor", "created_at", "message")
