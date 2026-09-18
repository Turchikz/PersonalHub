from rest_framework import serializers
from django.utils import timezone
from .models import Instrument, Verification


class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = (
            'id',
            'name',
            'type_model',
            'serial_number',
            'position',
            'functional_unit',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
        )

    def validate(self, attrs):
        status = attrs.get(
            "status",
            getattr(self.instance, "status", Instrument.Status.WORK),
        )
        position = attrs.get(
            "position",
            getattr(self.instance, "position", None),
        )

        if position:
            position = position.strip()

        if status == Instrument.Status.WORK:
            if not position:
                raise serializers.ValidationError(
                    {"position": "Укажите место установки."}
                )

            attrs["position"] = position
        else:
            attrs["position"] = None

        return attrs


class VerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Verification
        fields = (
            "id",
            "instrument",
            "verification_date",
            "valid_until",
            "next_verification_date",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        verification_date = attrs.get(
            "verification_date",
            getattr(self.instance, "verification_date", None),
        )
        valid_until = attrs.get(
            "valid_until",
            getattr(self.instance, "valid_until", None),
        )
        next_verification_date = attrs.get(
            "next_verification_date",
            getattr(self.instance, "next_verification_date", None),
        )

        errors = {}

        if verification_date > timezone.localdate():
            errors["verification_date"] = [
                "Дата поверки не может быть позже текущей даты."
            ]

        if valid_until <= verification_date:
            errors["valid_until"] = [
                "Дата окончания должна быть позже даты поверки."
            ]

        if (
            next_verification_date is not None
            and next_verification_date <= verification_date
        ):
            errors["next_verification_date"] = [
                "Следующая плановая поверка должна быть позже даты поверки."
            ]

        if errors:
            raise serializers.ValidationError(errors)
        return attrs