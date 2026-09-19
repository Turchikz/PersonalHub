import pytest
from rest_framework import status
from rest_framework.test import APIClient

from datetime import timedelta

from django.utils import timezone

from metrology.models import Instrument, Verification




@pytest.mark.django_db
def test_create_working_instrument():
    # Arrange
    client = APIClient()
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15200",
        "position": " PDT-2005 ",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    # Act
    response = client.post("/api/instruments/", data, format="json")

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["position"] == "PDT-2005"
    assert response.data["id"] is not None


@pytest.mark.django_db
def test_create_working_instrument_without_position_is_invalid():
    # Arrange
    client = APIClient()
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15201",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    # Act
    response = client.post("/api/instruments/", data, format="json")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "position" in response.data
    assert not Instrument.objects.filter(serial_number='15201').exists()


@pytest.mark.django_db
def test_spare_instrument_position_is_cleared():
    # Arrange
    client = APIClient()
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15201",
        "position": "PDT-2006",
        "functional_unit": "BIK",
        "status": "SPARE",
    }

    # Act
    response = client.post("/api/instruments/", data, format='json')

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["position"] is None

    instrument = Instrument.objects.get(id=response.data["id"])
    assert instrument.position is None


@pytest.mark.django_db
def test_instrument_change_status_work_to_repair_is_valid():
    # Arrange
    client = APIClient()

    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15202",
        position="PDT-2007",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )

    # Act
    response = client.patch(
        f"/api/instruments/{instrument.id}/",
        {"status": "REPAIR"},
        format="json",
    )

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == Instrument.Status.REPAIR
    assert response.data["position"] is None

    # Assert: проверяем фактическое состояние базы
    instrument.refresh_from_db()

    assert instrument.status == Instrument.Status.REPAIR
    assert instrument.position is None


@pytest.mark.django_db
def test_instrument_change_status_repair_to_work_without_position_is_invalid():
    # Arrange
    client = APIClient()

    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15203",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.REPAIR,
    )

    # Act
    response = client.patch(
        f"/api/instruments/{instrument.id}/",
        {"status": "WORK"},
        format="json",
    )

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "position" in response.data

    # Assert: проверяем фактическое состояние базы
    instrument.refresh_from_db()

    assert instrument.status == Instrument.Status.REPAIR
    assert instrument.position is None


@pytest.mark.django_db
def test_instrument_change_status_repair_to_work_with_position_is_valid():
    # Arrange
    client = APIClient()

    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15203",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.REPAIR,
    )

    # Act
    response = client.patch(
        f"/api/instruments/{instrument.id}/",
        {
            "status": Instrument.Status.WORK,
            "position": " PDT-2008 "
            },
        format="json",
    )

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == Instrument.Status.WORK
    assert response.data["position"] == "PDT-2008"

    # Assert: проверяем фактическое состояние базы
    instrument.refresh_from_db()

    assert instrument.status == Instrument.Status.WORK
    assert instrument.position == "PDT-2008"


@pytest.mark.django_db
def test_get_instrument_list():
    # Arrange
    client = APIClient()
    instrument_1 = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15204",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )
    instrument_2 = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15205",
        position="PDT-2009",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )

    # Act
    response = client.get("/api/instruments/")

    # Assert проверяем ответ API
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

    # Assert проверяем содержимое ответа API
    returned_ids = {item["id"] for item in response.data}

    assert returned_ids == {instrument_1.id, instrument_2.id}


@pytest.mark.django_db
def test_get_existing_instrument_returns_200():
    # Arrange
    client = APIClient()
    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15205",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    # Act
    response = client.get(f"/api/instruments/{instrument.id}/")

    # Assert проверяем ответ API
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == instrument.id
    assert response.data["serial_number"] == instrument.serial_number
    assert response.data["status"] == instrument.status


@pytest.mark.django_db
def test_get_nonexistent_instrument_returns_404():
    # Arrange
    client = APIClient()

    # Act
    response = client.get("/api/instruments/999999/")

    # Assert проверяем ответ API
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_delete_instrument():
    # Arrange
    client = APIClient()

    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15206",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    # Act
    response = client.delete(f"/api/instruments/{instrument.id}/")

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Instrument.objects.filter(id=instrument.id).exists()


@pytest.mark.django_db
def test_delete_instrument_with_verification_returns_409():
    # Arrange
    client = APIClient()

    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15207",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    today = timezone.localdate()

    Verification.objects.create(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=None,
    )

    # Act
    response = client.delete(f"/api/instruments/{instrument.id}/")

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert Instrument.objects.filter(id=instrument.id).exists()


@pytest.mark.django_db
def test_create_valid_verification(instrument):
    # Arrange
    client = APIClient()

    today = timezone.localdate()

    data = {
        "instrument": instrument.id,
        "verification_date": today.isoformat(),
        "valid_until": (today+timedelta(days=365)).isoformat(),
        "next_verification_date": None,
    }

    # Act
    response = client.post("/api/verifications/", data, format="json",)

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["instrument"] == instrument.id
    assert response.data["verification_date"] == today.isoformat()
    assert response.data["valid_until"] == (today+timedelta(days=365)).isoformat()
    assert response.data["next_verification_date"] is None

    # Assert: проверяем сохранённую запись
    verification = Verification.objects.get(id=response.data["id"])

    assert verification.instrument == instrument
    assert verification.verification_date == today
    assert verification.valid_until == today + timedelta(days=365)
    assert verification.next_verification_date is None


@pytest.mark.django_db
def test_create_verification_with_future_date_returns_400(instrument):
    # Arrange
    client = APIClient()

    today = timezone.localdate()

    data = {
        "instrument": instrument.id,
        "verification_date": (today + timedelta(days=1)).isoformat(),
        "valid_until": (today + timedelta(days=365)).isoformat(),
        "next_verification_date": None,
    }

    # Act
    response = client.post("/api/verifications/", data, format="json",)

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "verification_date" in response.data
    assert not Verification.objects.exists()


@pytest.mark.django_db
def test_patch_verification_with_invalid_valid_until_returns_400(instrument):
    # Arrange
    client = APIClient()

    today = timezone.localdate()

    verification = Verification.objects.create(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=None,
    )

    # Act
    response = client.patch(
        f"/api/verifications/{verification.id}/",
        {"valid_until": today.isoformat()},
        format="json",
    )

    # Assert проверка ответа по API
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "valid_until" in response.data

    # Assert проверка состояния базы данных
    verification.refresh_from_db()
    assert verification.valid_until == today + timedelta(days=365)


@pytest.mark.django_db
def test_filter_instruments_by_status():
    # Arrange
    client = APIClient()

    spare_instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15208",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )
    working_instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15209",
        position="PDT-2001",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )

    # Act
    response = client.get("/api/instruments/?status=WORK")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {working_instrument.id}


@pytest.mark.django_db
def test_filter_instruments_by_functional_unit():
    # Arrange
    client = APIClient()

    bik_instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15208",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )
    bil_instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15209",
        position="PDT-2001",
        functional_unit=Instrument.FunctionalUnit.BIL,
        status=Instrument.Status.WORK,
    )

    # Act
    response = client.get("/api/instruments/?functional_unit=BIK")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {bik_instrument.id}


@pytest.mark.django_db
def test_filter_instruments_by_functional_unit_and_status():
    # Arrange
    client = APIClient()

    bik_work_instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15208",
        position="PDT-2009",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )
    bik_spare_instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15209",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )
    bil_work_instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15210",
        position="PDT-2010",
        functional_unit=Instrument.FunctionalUnit.BIL,
        status=Instrument.Status.WORK,
    )

    # Act
    response = client.get(
        "/api/instruments/?functional_unit=BIK&status=WORK"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {bik_work_instrument.id}


@pytest.mark.django_db
def test_filter_verifications_by_instrument():
   # Arrange
    client = APIClient()

    instrument_1 = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15209",
        position="PDT-2010",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )
    instrument_2 = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15210",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    today = timezone.localdate()
    verification_1 = Verification.objects.create(
        instrument=instrument_1,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date = None,
    )

    verification_2 = Verification.objects.create(
        instrument=instrument_2,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=None,
    )

    # Act
    response = client.get(
        f"/api/verifications/?instrument={instrument_1.id}"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {verification_1.id}