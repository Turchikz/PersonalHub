from rest_framework import serializers

from .models import Instrument


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