import pytest

from metrology.serializers import InstrumentSerializer


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
