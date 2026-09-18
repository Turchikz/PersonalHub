import pytest

from datetime import timedelta

from django.utils import timezone

from metrology.serializers import InstrumentSerializer, VerificationSerializer


@pytest.mark.django_db
def test_valid_working_instrument_data_passes_serializer_validation():
    # Arrange
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15198",
        "position": "  PDT-2001  ",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    serializer = InstrumentSerializer(data=data)

    # Act
    is_valid = serializer.is_valid()

    # Assert
    assert is_valid, serializer.errors
    assert serializer.validated_data["position"] == "PDT-2001"


@pytest.mark.django_db
def test_working_instrument_without_position_fails_serializer_validation():
    # Arrange
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15198",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    serializer = InstrumentSerializer(data=data)

    # Act
    is_valid = serializer.is_valid()

    # Assert
    assert not is_valid
    assert "position" in serializer.errors


@pytest.mark.django_db
def test_spare_instrument_position_is_cleared_by_serializer():
    # Arrange
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15198",
        "position": "PDT-2002",
        "functional_unit": "BIK",
        "status": "SPARE",
    }

    serializer = InstrumentSerializer(data=data)

    # Act
    is_valid = serializer.is_valid()

    # Assert
    assert is_valid, serializer.errors
    assert serializer.validated_data["position"] is None


@pytest.mark.django_db
def test_valid_verification_passes_serializer_validation(instrument):
    # Arrange
    today = timezone.localdate()

    data = {
        "instrument": instrument.id,
        "verification_date": today.isoformat(),
        "valid_until": (today + timedelta(days=365)).isoformat(),
        "next_verification_date": (today + timedelta(days=350)).isoformat(),
    }

    serializer = VerificationSerializer(data=data)

    # Act
    is_valid = serializer.is_valid()

    # Assert
    assert is_valid, serializer.errors
    assert serializer.validated_data["instrument"] == instrument


@pytest.mark.django_db
def test_future_verification_date_fails_serializer_validation(instrument):
    # Arrange
    today = timezone.localdate()

    data = {
        "instrument": instrument.id,
        "verification_date": (today + timedelta(days=1)).isoformat(),
        "valid_until": (today + timedelta(days=365)).isoformat(),
        "next_verification_date": None,
    }

    # Act
    serializer = VerificationSerializer(data=data)
    is_valid = serializer.is_valid()

    # Assert
    assert not is_valid
    assert "verification_date" in serializer.errors
    assert str(serializer.errors["verification_date"][0]) == (
        "Дата поверки не может быть позже текущей даты."
    )


@pytest.mark.django_db
def test_valid_until_equal_to_verification_date_fails_validation(instrument):
    # Arrange
    today = timezone.localdate()

    data = {
        "instrument": instrument.id,
        "verification_date": today.isoformat(),
        "valid_until": today.isoformat(),
        "next_verification_date": None,
    }

    # Act
    serializer = VerificationSerializer(data=data)
    is_valid = serializer.is_valid()

    # Assert
    assert not is_valid
    assert "valid_until" in serializer.errors
    assert str(serializer.errors["valid_until"][0]) == (
        "Дата окончания должна быть позже даты поверки."
    )


@pytest.mark.django_db
def test_next_verification_date_equal_to_verification_date_fails_validation(instrument):
    # Arrange
    today = timezone.localdate()

    data = {
        "instrument": instrument.id,
        "verification_date": today.isoformat(),
        "valid_until": (today+timedelta(days=365)).isoformat(),
        "next_verification_date": today.isoformat(),
    }

    # Act
    serializer = VerificationSerializer(data=data)
    is_valid = serializer.is_valid()

    # Assert
    assert not is_valid
    assert "next_verification_date" in serializer.errors
    assert str(serializer.errors["next_verification_date"][0]) == (
        "Следующая плановая поверка должна быть позже даты поверки."
    )