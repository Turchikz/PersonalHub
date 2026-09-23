import pytest

from metrology.models import Instrument

from rest_framework.test import APIClient


@pytest.fixture
def instrument():
    return Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15195",
        position="PDT-2004",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )


@pytest.fixture
def authenticated_client(django_user_model):
    user = django_user_model.objects.create_user(
        username="test user",
    )
    client = APIClient()
    client.force_authenticate(user=user)

    return client


@pytest.fixture
def admin_client(django_user_model):
    admin = django_user_model.objects.create_user(
        username="admin_user",
        is_staff=True,
    )

    client = APIClient()
    client.force_authenticate(user=admin)

    return client
