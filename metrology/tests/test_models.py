from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from metrology.models import Instrument, Verification


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


@pytest.mark.django_db
def test_valid_verification_passes_validation(instrument):
    today = timezone.localdate()

    verification = Verification(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=today + timedelta(days=350),
    )

    # Act: отсутствие исключения означает успешную валидацию
    verification.full_clean()


@pytest.mark.django_db
def test_future_verification_date_is_invalid(instrument):
    today = timezone.localdate()

    verification = Verification(
        instrument=instrument,
        verification_date=today+timedelta(days=1),
        valid_until=today + timedelta(days=365),
        next_verification_date=today + timedelta(days=350),
    )

    # Act: запускается валидация и сохраняется ошибка
    with pytest.raises(ValidationError) as error:
        verification.full_clean()

    # Assert: ошибка относится именно к полю verification_date
    assert "verification_date" in error.value.message_dict


@pytest.mark.django_db
def test_valid_until_equal_verification_date_is_invalid(instrument):
    today = timezone.localdate()

    verification = Verification(
        instrument=instrument,
        verification_date=today,
        valid_until=today,
        next_verification_date=None,
    )

    # Act: запускается валидация и сохраняется ошибка
    with pytest.raises(ValidationError) as error:
        verification.full_clean()

    # Assert: ошибка относится именно к полю valid_until
    assert "valid_until" in error.value.message_dict


@pytest.mark.django_db
def test_next_verification_date_equal_verification_date_is_invalid(instrument):
    today = timezone.localdate()

    verification = Verification(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=today,
    )

    # Act: запускается валидация и сохраняется ошибка
    with pytest.raises(ValidationError) as error:
        verification.full_clean()

    # Assert: ошибка относится именно к полю next_verification_date
    assert "next_verification_date" in error.value.message_dict


@pytest.mark.django_db
def test_verification_without_next_date_is_valid(instrument):
    # Arrange
    today = timezone.localdate()

    verification = Verification(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=None,
    )

    # Act
    verification.full_clean()

    # Assert
    assert verification.next_verification_date is None