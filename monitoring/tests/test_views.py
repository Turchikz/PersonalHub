from unittest.mock import patch

import pytest
from django.urls import reverse

from monitoring.models import Monitor, MonitorNotification, MonitorState

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def static_storage(settings):
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


def test_dashboard_and_polling_only_read_saved_results(client):
    Monitor.objects.all().delete()
    Monitor.objects.create(name="Rozetked", url="https://rozetked.me/", state=MonitorState.ONLINE)
    with patch("monitoring.services.probe_url") as probe:
        page = client.get(reverse("home"))
        response = client.get(reverse("monitoring:status"))
    assert page.status_code == 200 and response.status_code == 200
    assert "Web Monitor" in page.content.decode()
    assert "Онлайн" in response.json()["html"]
    assert response.json()["notifications"] == []
    assert "no-store" in response.headers["Cache-Control"]
    probe.assert_not_called()


def test_notification_history_and_escaped_content(client):
    Monitor.objects.all().delete()
    monitor = Monitor.objects.create(name="<script>alert(1)</script>", url="https://rozetked.me/")
    MonitorNotification.objects.create(
        monitor=monitor, previous_state=MonitorState.ONLINE, state=MonitorState.RESTRICTED,
        message="<img src=x onerror=alert(1)>",
    )
    data = client.get(reverse("monitoring:status")).json()
    assert "&lt;script&gt;" in data["html"]
    assert "&lt;img" in data["html"]
    assert "<img src=x" not in data["html"]
    assert len(data["notifications"]) == 1


def test_status_endpoint_rejects_post(client):
    assert client.post(reverse("monitoring:status")).status_code == 405


def test_admin_settings_requires_staff(client, django_user_model):
    user = django_user_model.objects.create_user(username="user", password="test-password")
    client.force_login(user)
    response = client.get(reverse("admin:monitoring_monitor_changelist"))
    assert response.status_code == 302
