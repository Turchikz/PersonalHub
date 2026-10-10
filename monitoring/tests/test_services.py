from datetime import timedelta
from http.client import RemoteDisconnected
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone

from monitoring.models import CheckResult, Monitor, MonitorNotification, MonitorState
from monitoring.services import HTTPResult, check_monitor, classify, probe_url, probe_with_retry

pytestmark = pytest.mark.django_db


@pytest.fixture
def monitor():
    Monitor.objects.all().delete()
    return Monitor.objects.create(name="Rozetked", url="https://rozetked.me/")


@pytest.mark.parametrize("target,control,state", [
    (HTTPResult(200, 10), HTTPResult(), MonitorState.ONLINE),
    (HTTPResult(204, 10), HTTPResult(), MonitorState.ONLINE),
    (HTTPResult(403, 10), HTTPResult(200, 10), MonitorState.SITE_DOWN),
    (HTTPResult(503, 10), HTTPResult(200, 10), MonitorState.SITE_DOWN),
    (HTTPResult(error="timeout"), HTTPResult(200, 10), MonitorState.RESTRICTED),
    (HTTPResult(error="timeout"), HTTPResult(error="DNS"), MonitorState.NETWORK_DOWN),
    (HTTPResult(error="timeout"), HTTPResult(500, 10), MonitorState.NETWORK_DOWN),
])
def test_classification(target, control, state):
    assert classify(target, control) == state


def test_transitions_notify_once_and_recovery(monitor):
    with patch("monitoring.services.probe_with_retry", return_value=HTTPResult(200, 42)) as probe:
        result = check_monitor(monitor.pk)
        assert result.is_up
        assert probe.call_count == 1
    assert not MonitorNotification.objects.exists()  # First result is a baseline.

    def run_with(target, control=None):
        Monitor.objects.filter(pk=monitor.pk).update(next_check_at=timezone.now())
        responses = [target] if target.is_up else [target, control]
        with patch("monitoring.services.probe_with_retry", side_effect=responses):
            return check_monitor(monitor.pk)

    run_with(HTTPResult(error="timeout"), HTTPResult(200, 18))
    notification = MonitorNotification.objects.get()
    assert notification.previous_state == MonitorState.ONLINE
    assert notification.state == MonitorState.RESTRICTED
    assert "возможны" in notification.message
    run_with(HTTPResult(error="timeout"), HTTPResult(200, 18))
    assert MonitorNotification.objects.count() == 1
    run_with(HTTPResult(200, 24))
    assert MonitorNotification.objects.count() == 2
    assert "признаки белых списков исчезли" in MonitorNotification.objects.first().message
    assert CheckResult.objects.count() == 4


def test_due_time_inactive_and_no_duplicate_check(monitor):
    with patch("monitoring.services.probe_with_retry", return_value=HTTPResult(200, 1)) as probe:
        check_monitor(monitor.pk)
        assert check_monitor(monitor.pk) is None
        assert probe.call_count == 1
        monitor.refresh_from_db()
        assert monitor.next_check_at == monitor.last_checked_at + timedelta(minutes=15)
        Monitor.objects.filter(pk=monitor.pk).update(is_active=False, next_check_at=timezone.now())
        assert check_monitor(monitor.pk) is None


def test_history_retains_urls_and_network_errors(monitor):
    with patch("monitoring.services.probe_with_retry", side_effect=[
        HTTPResult(error="timeout"), HTTPResult(error="DNS failure"),
    ]):
        result = check_monitor(monitor.pk)
    assert result.state == MonitorState.NETWORK_DOWN
    assert result.status_code is None and result.response_time_ms is None
    assert result.error_message == "timeout" and result.control_error_message == "DNS failure"
    Monitor.objects.filter(pk=monitor.pk).update(url="https://example.org/")
    result.refresh_from_db()
    assert result.url == "https://rozetked.me/"


def test_custom_interval_and_command_once(monitor):
    Monitor.objects.filter(pk=monitor.pk).update(interval_minutes=7)
    with patch("monitoring.services.probe_with_retry", return_value=HTTPResult(200, 1)):
        call_command("run_monitors", "--once")
    monitor.refresh_from_db()
    assert monitor.next_check_at == monitor.last_checked_at + timedelta(minutes=7)


def test_retry_discards_transient_failure():
    with patch("monitoring.services.probe_url", side_effect=[HTTPResult(error="timeout"), HTTPResult(200, 3)]) as probe:
        assert probe_with_retry("https://example.org/", 4).is_up
        assert probe.call_count == 2


@pytest.mark.parametrize("error", [URLError("DNS"), TimeoutError("timeout"), RemoteDisconnected("disconnected")])
def test_transport_failures_are_not_http_responses(error):
    with patch("monitoring.services.build_opener") as build:
        build.return_value.open.side_effect = error
        result = probe_url("https://example.org/", 2)
    assert result.status_code is None and result.response_time_ms is None
    assert result.error


def test_http_error_is_preserved_and_closed():
    error = HTTPError("https://example.org/", 403, "Forbidden", {}, MagicMock())
    with patch("monitoring.services.build_opener") as build:
        build.return_value.open.side_effect = error
        result = probe_url("https://example.org/", 2)
    assert result.status_code == 403 and result.error.startswith("HTTP 403")
    assert not result.is_up
    assert error.closed


def test_redirect_loop_is_not_online():
    error = HTTPError("https://example.org/", 302, "redirect loop", {}, MagicMock())
    with patch("monitoring.services.build_opener") as build:
        build.return_value.open.side_effect = error
        result = probe_url("https://example.org/", 2)
    assert not result.is_up
    assert classify(result, HTTPResult(200, 1)) == MonitorState.SITE_DOWN


def test_http_success_closes_response_and_honors_timeout():
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response
    with patch("monitoring.services.build_opener") as build:
        build.return_value.open.return_value = response
        result = probe_url("https://example.org/", 7)
        assert build.return_value.open.call_args.kwargs["timeout"] == 7
    assert result.is_up and result.response_time_ms is not None
    response.__exit__.assert_called_once()
    response.read.assert_not_called()


@pytest.mark.parametrize("field,value", [("url", "ftp://example.org/"), ("interval_minutes", 0), ("timeout_seconds", 60), ("control_url", "https://rozetked.me/")])
def test_invalid_monitor_settings(monitor, field, value):
    setattr(monitor, field, value)
    with pytest.raises(ValidationError):
        monitor.full_clean()


def test_stale_and_paused_do_not_claim_online(monitor):
    monitor.state = MonitorState.ONLINE
    monitor.last_checked_at = timezone.now() - timedelta(hours=1)
    assert monitor.display_state == "stale"
    monitor.is_active = False
    assert monitor.display_state == "paused"
