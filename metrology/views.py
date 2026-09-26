from rest_framework import status, viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
)
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.deletion import ProtectedError


from .models import Instrument, Verification
from .permissions import MetrologyPermission
from .serializers import InstrumentSerializer, VerificationSerializer


class InstrumentViewSet(viewsets.ModelViewSet):
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [MetrologyPermission]
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "functional_unit"]

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


class VerificationViewSet(viewsets.ModelViewSet):
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
    ]
    permission_classes = [MetrologyPermission]
    queryset = Verification.objects.all()
    serializer_class = VerificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["instrument"]
