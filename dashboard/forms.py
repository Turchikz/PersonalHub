from django import forms

from dashboard.models import CountdownEvent


class CountdownEventForm(forms.ModelForm):
    class Meta:
        model = CountdownEvent
        fields = ("title", "target_datetime")

        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "Название события",
                }
            ),
            "target_datetime": forms.DateTimeInput(
                format="%Y-%m-%dT%H:%M",
                attrs={
                    "type": "datetime-local",
                },
            ),
        }