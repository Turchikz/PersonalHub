from django.contrib import admin

from .models import Instrument, Verification


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("name", "type_model", "serial_number", "position", "functional_unit", "status")
    search_fields = ("name", "type_model", "serial_number", "position")
    list_filter = ("functional_unit", "status")
    ordering = ("name", "type_model", "serial_number")
    list_display_links = ("name", "type_model", "serial_number")

@admin.register(Verification)
class VerificationAdmin(admin.ModelAdmin):
    list_display = ("instrument", "verification_date", "valid_until", "next_verification_date")
    search_fields = ("instrument__name", "instrument__type_model", "instrument__serial_number")
    list_filter = ("verification_date", "valid_until")
    ordering = ("-verification_date", "valid_until")
    date_hierarchy = "verification_date"