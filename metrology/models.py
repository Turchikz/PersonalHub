from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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
        ordering = ["name", "type_model", "serial_number"]  # noqa: RUF012
        constraints = [  # noqa: RUF012
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
                raise ValidationError(
                    {"position": "Укажите место установки"}
                )
            
        else:
            self.position = None

    def __str__(self):
        return f"{self.name} {self.type_model} №{self.serial_number}"
    

class Verification(models.Model):
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.PROTECT,
        related_name="verifications",
    )

    verification_date = models.DateField()
    valid_until = models.DateField()    
    next_verification_date = models.DateField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-verification_date"]

    def clean(self):
        super().clean()

        errors = {}

        if (
            self.verification_date
            and self.verification_date > timezone.localdate()
        ):
            errors["verification_date"] = (
                "Дата поверки не может быть позже текущей даты."
            )

        if (
            self.verification_date
            and self.valid_until
            and self.valid_until <= self.verification_date
        ):
            errors["valid_until"] = (
                "Дата окончания должна быть позже даты поверки."
            )

        if (
            self.verification_date
            and self.next_verification_date
            and self.next_verification_date <= self.verification_date
        ):
            errors["next_verification_date"] = (
                "Следующая плановая поверка должна быть позже даты поверки."
            )

        if errors:
            raise ValidationError(errors)
        
    def __str__(self):
        return f"{self.instrument.name} {self.instrument.type_model} №{self.instrument.serial_number} — {self.verification_date}"