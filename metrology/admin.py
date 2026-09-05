from django.contrib import admin

from .models import Instrument

@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("name", "type_model", "serial_number", "position", "functional_unit", "status")
    search_fields = ("name", "type_model", "serial_number", "position")
    list_filter = ("functional_unit", "status")
    ordering = ("name", "type_model", "serial_number")
    list_display_links = ("name", "type_model", "serial_number")

    class Meta:
        ordering = ("name", "type_model", "serial_number")
