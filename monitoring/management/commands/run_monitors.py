import signal
from threading import Event

from django.core.management.base import BaseCommand
from django.db import close_old_connections

from monitoring.services import check_due_monitors


class Command(BaseCommand):
    help = "Проверять активные мониторы по настроенному расписанию"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Выполнить один проход и выйти")

    def handle(self, *args, **options):
        if options["once"]:
            self.stdout.write(f"Выполнено проверок: {check_due_monitors()}")
            return
        stop = Event()
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, lambda *_: stop.set())
        self.stdout.write("Web Monitor запущен")
        while not stop.is_set():
            close_old_connections()
            count = check_due_monitors()
            if count:
                self.stdout.write(f"Выполнено проверок: {count}")
            stop.wait(10)
