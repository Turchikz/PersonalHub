from django.urls import path

from dashboard.views import event_speak, home, delete_event, edit_event


urlpatterns = [
    path("", home, name="home"),
    path("events/<int:event_id>/speak/", event_speak, name="event_speak"),
    path("events/<int:event_id>/delete/", delete_event, name="delete_event"),
    path("events/<int:event_id>/edit/", edit_event, name="edit_event"),
]
