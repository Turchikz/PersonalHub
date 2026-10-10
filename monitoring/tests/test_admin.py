from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.contrib.admin import AdminSite
from django.utils import timezone

from monitoring.admin import MonitorAdmin
from monitoring.models import Monitor, MonitorState

pytestmark = pytest.mark.django_db


def test_save_preserves_state_written_while_admin_form_was_open():
    obj = Monitor.objects.create(name="Test", url="https://example.org/")
    checked_at = timezone.now()
    Monitor.objects.filter(pk=obj.pk).update(state=MonitorState.RESTRICTED, last_checked_at=checked_at)
    obj.interval_minutes = 7
    MonitorAdmin(Monitor, AdminSite()).save_model(None, obj, SimpleNamespace(changed_data=["interval_minutes"]), True)
    obj.refresh_from_db()
    assert obj.state == MonitorState.RESTRICTED and obj.last_checked_at == checked_at
    assert obj.next_check_at <= timezone.now()


def test_url_change_resets_baseline_and_schedules_check():
    obj = Monitor.objects.create(
        name="Test", url="https://example.org/", state=MonitorState.ONLINE,
        last_checked_at=timezone.now(), next_check_at=timezone.now() + timedelta(hours=1),
    )
    obj.url = "https://example.com/"
    MonitorAdmin(Monitor, AdminSite()).save_model(None, obj, SimpleNamespace(changed_data=["url"]), True)
    obj.refresh_from_db()
    assert obj.state == MonitorState.UNKNOWN and obj.last_checked_at is None
    assert obj.next_check_at <= timezone.now()
