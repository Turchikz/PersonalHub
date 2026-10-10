from datetime import timedelta
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, URLValidator
from django.db import models
from django.utils import timezone


class MonitorState(models.TextChoices):
    UNKNOWN = "unknown", "Ещё не проверен"
    ONLINE = "online", "Онлайн"
    RESTRICTED = "restricted", "Возможны белые списки"
    SITE_DOWN = "site_down", "Сайт недоступен"
    NETWORK_DOWN = "network_down", "Проблема подключения"


class Monitor(models.Model):
    name = models.CharField("Название", max_length=100)
    url = models.URLField("Проверяемый сайт", max_length=2048,
                          validators=[URLValidator(schemes=["http", "https"])])
    control_url = models.URLField(
        "Контрольный сайт", max_length=2048, default="https://ya.ru/",
        validators=[URLValidator(schemes=["http", "https"])],
        help_text="Укажите сайт, доступный у вашего оператора при белых списках.",
    )
    interval_minutes = models.PositiveIntegerField(
        "Интервал, минут", default=15,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
    )
    timeout_seconds = models.PositiveSmallIntegerField(
        "Таймаут, секунд", default=10,
        validators=[MinValueValidator(1), MaxValueValidator(30)],
    )
    is_active = models.BooleanField("Проверки включены", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    state = models.CharField("Состояние", max_length=20,
                             choices=MonitorState.choices, default=MonitorState.UNKNOWN)
    last_checked_at = models.DateTimeField("Последняя проверка", null=True, blank=True)
    next_check_at = models.DateTimeField("Следующая проверка", default=timezone.now)

    class Meta:
        ordering = ["pk"]
        verbose_name = "Монитор"
        verbose_name_plural = "Мониторы"

    def __str__(self):
        return self.name

    def clean(self):
        if self.url and self.control_url and urlsplit(self.url).hostname == urlsplit(self.control_url).hostname:
            raise ValidationError({"control_url": "Контрольный сайт должен отличаться от проверяемого."})

    @property
    def display_state(self):
        if not self.is_active:
            return "paused"
        if self.last_checked_at and timezone.now() > (
            self.last_checked_at + timedelta(minutes=self.interval_minutes * 2, seconds=60)
        ):
            return "stale"
        return self.state

    @property
    def display_label(self):
        return {"paused": "Приостановлен", "stale": "Проверки устарели"}.get(
            self.display_state, self.get_state_display()
        )


class CheckResult(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name="checks")
    checked_at = models.DateTimeField("Время проверки", default=timezone.now)
    url = models.URLField(max_length=2048)
    control_url = models.URLField(max_length=2048)
    status_code = models.PositiveSmallIntegerField("HTTP", null=True, blank=True)
    response_time_ms = models.PositiveIntegerField("Время ответа, мс", null=True, blank=True)
    is_up = models.BooleanField("Сайт доступен")
    error_message = models.TextField("Ошибка сайта", blank=True)
    control_status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    control_error_message = models.TextField(blank=True)
    state = models.CharField("Состояние", max_length=20, choices=MonitorState.choices)

    class Meta:
        ordering = ["-checked_at", "-pk"]
        indexes = [models.Index(fields=["monitor", "-checked_at"])]
        verbose_name = "Проверка"
        verbose_name_plural = "История проверок"

    def __str__(self):
        return f"{self.monitor}: {self.get_state_display()}"


class MonitorNotification(models.Model):
    monitor = models.ForeignKey(Monitor, on_delete=models.CASCADE, related_name="notifications")
    created_at = models.DateTimeField("Время", default=timezone.now)
    previous_state = models.CharField(max_length=20, choices=MonitorState.choices)
    state = models.CharField(max_length=20, choices=MonitorState.choices)
    message = models.CharField("Уведомление", max_length=500)

    class Meta:
        ordering = ["-pk"]
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления Web Monitor"

    def __str__(self):
        return self.message
