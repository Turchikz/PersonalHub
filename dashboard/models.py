from django.db import models

class CountdownEvent(models.Model):
    title = models.CharField(max_length=100)
    target_datetime = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title