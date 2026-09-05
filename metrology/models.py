from django.core.exceptions import ValidationError
from django.db import models



class Instrument(models.Model):
    class FunctionalUnit(models.TextChoices):
        BIL = "BIL", "БИЛ"
        BIK = "BIK", "БИК"
        CONTROL_ROOM = "CONTROL_ROOM", "Аппаратная"
        BSE = "BSE", "БСЭ"

    class Status(models.TextChoices):
        WORK = "WORK", "В работе"
        SPARE = "SPARE", "ЗИП"
        REPAIR = "REPAIR", "В ремонте"
        VERIFICATION = "VERIFICATION", "На поверке"

    name = models.CharField(max_length=255)
    type_model = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=20)
    position = models.CharField(max_length=20, unique=True, blank=True, null=True)

    functional_unit = models.CharField(
        max_length=20,
        choices=FunctionalUnit.choices,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WORK,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "type_model", "serial_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["type_model", "serial_number"],
                name="unique_instrument_type_model_serial_number",
            ),
        ]
    def clean(self):
        # сначала выполнить все родительские проверки
        super().clean()
        

        # персональные проверки
        if self.position:
            self.position = self.position.strip()

        if self.status == self.Status.WORK:
            if not self.position:
                raise ValidationError("Укажите место установки")
            
        else:
            self.position = None

    def __str__(self):
        return f"{self.name} {self.type_model} №{self.serial_number}"