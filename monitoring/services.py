"""HTTP checks run in a worker, never as a side effect of a page visit."""
import logging
from dataclasses import dataclass
from datetime import timedelta
from http.client import HTTPException
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from django.db import transaction
from django.utils import timezone

from .models import CheckResult, Monitor, MonitorNotification, MonitorState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HTTPResult:
    status_code: int | None = None
    response_time_ms: int | None = None
    error: str = ""

    @property
    def is_up(self):
        return self.status_code is not None and 200 <= self.status_code < 400 and not self.error


class HTTPOnlyRedirectHandler(HTTPRedirectHandler):
    max_redirections = 3

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urlsplit(newurl).scheme not in {"http", "https"}:
            raise URLError("Редирект разрешён только на HTTP/HTTPS")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def probe_url(url, timeout):
    """Time to response headers; don't download entire pages or use env proxies."""
    if urlsplit(url).scheme not in {"http", "https"}:
        return HTTPResult(error="Разрешены только HTTP/HTTPS адреса")
    started = perf_counter()
    opener = build_opener(ProxyHandler({}), HTTPOnlyRedirectHandler())
    http_error = ""
    try:
        request = Request(url, headers={"User-Agent": "PersonalHub-WebMonitor/1.0"})
        with opener.open(request, timeout=timeout) as response:
            status = response.status
    except HTTPError as error:
        status = error.code
        http_error = f"HTTP {status}: {error.reason}"
        error.close()
    except (URLError, OSError, HTTPException, ValueError, UnicodeError) as error:
        return HTTPResult(error=str(error)[:1000])
    elapsed = round((perf_counter() - started) * 1000)
    return HTTPResult(status, elapsed, http_error or ("" if 200 <= status < 400 else f"HTTP {status}"))


def probe_with_retry(url, timeout):
    result = probe_url(url, timeout)
    if not result.is_up:
        result = probe_url(url, timeout)
    return result


def classify(target, control):
    if target.is_up:
        return MonitorState.ONLINE
    if target.status_code is not None:
        # A 403/404/5xx response alone does not indicate whitelist mode.
        return MonitorState.SITE_DOWN
    if control.is_up:
        return MonitorState.RESTRICTED
    return MonitorState.NETWORK_DOWN


def notification_message(monitor, previous, state):
    prefix = f"{monitor.name}: "
    if state == MonitorState.ONLINE:
        if previous == MonitorState.RESTRICTED:
            return prefix + "доступ восстановлен; признаки белых списков исчезли."
        return prefix + "сайт снова доступен."
    if state == MonitorState.RESTRICTED:
        return prefix + "сайт не отвечает, контрольный сайт доступен — возможны белые списки."
    if state == MonitorState.SITE_DOWN:
        return prefix + "сайт возвращает ошибку HTTP."
    return prefix + "проверяемый и контрольный сайты недоступны; проверьте подключение."


def check_monitor(monitor_id):
    """Serialize workers for one monitor; don't duplicate state-change notifications."""
    with transaction.atomic():
        monitor = Monitor.objects.select_for_update().get(pk=monitor_id)
        now = timezone.now()
        if not monitor.is_active or monitor.next_check_at > now:
            return None
        # Admin validation is also enforced for programmatically created monitors.
        monitor.full_clean()
        target = probe_with_retry(monitor.url, monitor.timeout_seconds)
        control = HTTPResult()
        if not target.is_up:
            control = probe_with_retry(monitor.control_url, monitor.timeout_seconds)
        state = classify(target, control)
        checked_at = timezone.now()
        result = CheckResult.objects.create(
            monitor=monitor, checked_at=checked_at,
            url=monitor.url, control_url=monitor.control_url,
            status_code=target.status_code, response_time_ms=target.response_time_ms,
            is_up=target.is_up, error_message=target.error,
            control_status_code=control.status_code, control_error_message=control.error,
            state=state,
        )
        if monitor.state != MonitorState.UNKNOWN and monitor.state != state:
            MonitorNotification.objects.create(
                monitor=monitor, previous_state=monitor.state, state=state,
                message=notification_message(monitor, monitor.state, state),
            )
        monitor.state = state
        monitor.last_checked_at = checked_at
        monitor.next_check_at = checked_at + timedelta(minutes=monitor.interval_minutes)
        monitor.save(update_fields=["state", "last_checked_at", "next_check_at"])
        return result


def check_due_monitors():
    ids = list(Monitor.objects.filter(is_active=True, next_check_at__lte=timezone.now())
               .values_list("pk", flat=True))
    count = 0
    for monitor_id in ids:
        try:
            if check_monitor(monitor_id) is not None:
                count += 1
        except Monitor.DoesNotExist:
            continue
        except Exception:
            logger.exception("Could not check monitor %s", monitor_id)
    return count
