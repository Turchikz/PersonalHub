import pytest
from django.core.exceptions import ValidationError

from metrology.models import Instrument


@pytest.mark.django_db
def test_working_instrument_with_position_is_valid():
    # Arrange
    instrument = Instrument(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15190",
        position="PDT-2001",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )

    # Act: отсутствие исключения означает успешную валидацию
    instrument.full_clean()


@pytest.mark.django_db
def test_working_instrument_without_position_is_invalid():
    # Arrange: создаётся СИ в работе без позиционного обозначения
    instrument = Instrument(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15191",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )

    # Act: запускается валидация и сохраняется исключение
    with pytest.raises(ValidationError) as error:
        instrument.full_clean()

    # Assert: ошибка относится именно к полю position
    assert "position" in error.value.message_dict


@pytest.mark.django_db
def test_repair_instrument_position_is_cleared():
    # Arrange обнуление позиции при статусе "в ремонте"
    instrument = Instrument(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15192",
        position="PDT-2002",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.REPAIR,
    )

    # Act
    instrument.full_clean()

    # Assert
    assert instrument.position is None


@pytest.mark.django_db
def test_spare_instrument_without_position_is_valid():
    # Arrange: создаётся резервное СИ без позиции
    instrument = Instrument(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15193",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    # Act
    instrument.full_clean()

    # Assert
    assert instrument.position is None


@pytest.mark.django_db
def test_instrument_position_is_stripped():
    # Arrange: создаётся СИ в работе с пробелами вокруг позиции
    instrument = Instrument(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15194",
        position=" PDT-2003 ",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )

    # Act
    instrument.full_clean()

    # Assert
    assert instrument.position == "PDT-2003"