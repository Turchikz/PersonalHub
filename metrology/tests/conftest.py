import pytest

from metrology.models import Instrument


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