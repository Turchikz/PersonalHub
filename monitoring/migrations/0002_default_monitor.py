from django.db import migrations


def add_default_monitor(apps, schema_editor):
    Monitor = apps.get_model("monitoring", "Monitor")
    Monitor.objects.using(schema_editor.connection.alias).create(
        name="Rozetked", url="https://rozetked.me/", control_url="https://ya.ru/",
        interval_minutes=15, timeout_seconds=10,
    )


class Migration(migrations.Migration):
    dependencies = [("monitoring", "0001_initial")]
    operations = [migrations.RunPython(add_default_monitor, migrations.RunPython.noop)]
