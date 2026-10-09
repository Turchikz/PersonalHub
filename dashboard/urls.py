from django.urls import path

from dashboard.views import event_speak, home


urlpatterns = [
    path("", home, name="home"),
    path("events/<int:event_id>/speak/", event_speak, name="event_speak"),
]
