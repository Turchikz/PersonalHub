from django.contrib import admin

from dashboard.models import CountdownEvent

@admin.register(CountdownEvent)
class CountdownEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_datetime', 'created_at')
    search_fields = ('title',)
