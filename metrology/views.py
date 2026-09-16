from rest_framework import status, viewsets
from rest_framework.response import Response
from django.db.models.deletion import ProtectedError


from .models import Instrument
from .serializers import InstrumentSerializer


class InstrumentViewSet(viewsets.ModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer

    def destroy(self, request, *args, **kwargs):
        instrument = self.get_object()

        try:
            self.perform_destroy(instrument)
        except ProtectedError:
            return Response(
                {
                    "detail": (
                        "Нельзя удалить средство измерений, "
                        "для которого существуют поверки."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)