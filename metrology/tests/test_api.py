import pytest
from rest_framework import status
from rest_framework.test import APIClient

from datetime import timedelta

from django.utils import timezone

from metrology.models import Instrument, Verification


@pytest.mark.django_db
def test_create_working_instrument(authenticated_client):
    # Arrange
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15200",
        "position": " PDT-2005 ",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    # Act
    response = authenticated_client.post("/api/instruments/", data, format="json")

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["position"] == "PDT-2005"
    assert response.data["id"] is not None


@pytest.mark.django_db
def test_create_working_instrument_without_position_is_invalid(authenticated_client):
    # Arrange
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15201",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    # Act
    response = authenticated_client.post("/api/instruments/", data, format="json")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "position" in response.data
    assert not Instrument.objects.filter(serial_number='15201').exists()


@pytest.mark.django_db
def test_spare_instrument_position_is_cleared(authenticated_client):
    # Arrange
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "15201",
        "position": "PDT-2006",
        "functional_unit": "BIK",
        "status": "SPARE",
    }

    # Act
    response = authenticated_client.post("/api/instruments/", data, format='json')

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["position"] is None

    instrument = Instrument.objects.get(id=response.data["id"])
    assert instrument.position is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "instrument_status",

    [
        Instrument.Status.REPAIR,
        Instrument.Status.SPARE,
        Instrument.Status.VERIFICATION,
    ],
)
def test_instrument_change_status_work_to_repair_spare_verification_is_valid(
    instrument_status,
    authenticated_client
    ):
    # Arrange
    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15202",
        position="PDT-2007",
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.WORK,
    )

    # Act
    response = authenticated_client.patch(
            f"/api/instruments/{instrument.pk}/",
            {"status": instrument_status},
            format="json",
        )

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_200_OK
    assert response.data["status"] == instrument_status
    assert response.data["position"] is None

    # Assert: проверяем фактическое состояние базы
    instrument.refresh_from_db()

    assert instrument.status == instrument_status
    assert instrument.position is None


@pytest.mark.django_db
def test_instrument_change_status_repair_to_work_without_position_is_invalid(authenticated_client):
    # Arrange
    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15203",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.REPAIR,
    )

    # Act
    response = authenticated_client.patch(
        f"/api/instruments/{instrument.pk}/",
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
def test_instrument_change_status_repair_to_work_with_position_is_valid(authenticated_client):
    # Arrange
    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15203",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.REPAIR,
    )

    # Act
    response = authenticated_client.patch(
        f"/api/instruments/{instrument.pk}/",
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

    assert returned_ids == {instrument_1.pk, instrument_2.pk}


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
    response = client.get(f"/api/instruments/{instrument.pk}/")

    # Assert проверяем ответ API
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == instrument.pk
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
def test_delete_instrument(authenticated_client):
    # Arrange
    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="15206",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    # Act
    response = authenticated_client.delete(f"/api/instruments/{instrument.pk}/")

    # Assert
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Instrument.objects.filter(id=instrument.pk).exists()


@pytest.mark.django_db
def test_delete_instrument_with_verification_returns_409(instrument,
                                                         admin_client):
    # Arrange

    today = timezone.localdate()

    Verification.objects.create(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=None,
    )

    # Act
    response = admin_client.delete(f"/api/instruments/{instrument.pk}/")

    # Assert
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.data["detail"] == (
        "Нельзя удалить средство измерений, "
        "для которого существуют поверки."
    )
    assert Instrument.objects.filter(id=instrument.pk).exists()


@pytest.mark.django_db
def test_create_valid_verification(
    instrument,
    authenticated_client
    ):
    # Arrange
    today = timezone.localdate()

    data = {
        "instrument": instrument.pk,
        "verification_date": today.isoformat(),
        "valid_until": (today+timedelta(days=365)).isoformat(),
        "next_verification_date": None,
    }

    # Act
    response = authenticated_client.post("/api/verifications/", data, format="json",)

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["instrument"] == instrument.pk
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
def test_create_verification_with_future_date_returns_400(
    instrument,
    authenticated_client
    ):
    # Arrange
    today = timezone.localdate()

    data = {
        "instrument": instrument.pk,
        "verification_date": (today + timedelta(days=1)).isoformat(),
        "valid_until": (today + timedelta(days=365)).isoformat(),
        "next_verification_date": None,
    }

    # Act
    response = authenticated_client.post("/api/verifications/", data, format="json",)

    # Assert: проверяем ответ API
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "verification_date" in response.data
    assert not Verification.objects.exists()


@pytest.mark.django_db
def test_patch_verification_with_invalid_valid_until_returns_400(
    instrument,
    authenticated_client
    ):
    # Arrange
    today = timezone.localdate()

    verification = Verification.objects.create(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=None,
    )

    # Act
    response = authenticated_client.patch(
        f"/api/verifications/{verification.pk}/",
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
    assert {item["id"] for item in response.data} == {working_instrument.pk}


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
    assert {item["id"] for item in response.data} == {bik_instrument.pk}


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
    assert {item["id"] for item in response.data} == {bik_work_instrument.pk}


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
        f"/api/verifications/?instrument={instrument_1.pk}"
    )

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert {item["id"] for item in response.data} == {verification_1.pk}


@pytest.mark.django_db
def test_anonymous_user_cannot_create_instrument():
    client = APIClient()
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "16001",
        "position": "PDT-3001",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    response = client.post(
        "/api/instruments/",
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Instrument.objects.filter(
        serial_number="16001"
    ).exists()


@pytest.mark.django_db
def test_create_working_instrument_authenticated(authenticated_client):
    data = {
        "name": "Датчик давления",
        "type_model": "ЭМИС БАР 143",
        "serial_number": "16001",
        "position": "PDT-3001",
        "functional_unit": "BIK",
        "status": "WORK",
    }

    response = authenticated_client.post(
        "/api/instruments/",
        data=data,
        format="json",
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Instrument.objects.filter(
        serial_number="16001"
    ).exists()


@pytest.mark.django_db
def test_admin_can_delete_instrument(admin_client):
    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="16002",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    response = admin_client.delete(
        f"/api/instruments/{instrument.pk}/"
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Instrument.objects.filter(pk=instrument.pk).exists()


@pytest.mark.django_db
def test_regular_user_cannot_delete_instrument(
    authenticated_client,
):
    instrument = Instrument.objects.create(
        name="Датчик давления",
        type_model="ЭМИС БАР 143",
        serial_number="16003",
        position=None,
        functional_unit=Instrument.FunctionalUnit.BIK,
        status=Instrument.Status.SPARE,
    )

    response = authenticated_client.delete(
        f"/api/instruments/{instrument.pk}/"
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Instrument.objects.filter(pk=instrument.pk).exists()


@pytest.mark.django_db
def test_anonymous_user_cannot_create_verification(instrument):
    client = APIClient()

    today = timezone.localdate()
    data = {
        "instrument": instrument.pk,
        "verification_date": today.isoformat(),
        "valid_until": (today + timedelta(days=365)).isoformat(),
        "next_verification_date": None,
    }

    response = client.post(
        "/api/verifications/",
        data=data,
        format="json",
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert not Verification.objects.filter(instrument=instrument.pk).exists()


@pytest.mark.django_db
def test_authenticated_user_can_create_verification(
    instrument,
    authenticated_client,
):
    today = timezone.localdate()
    data = {
        "instrument": instrument.pk,
        "verification_date": today.isoformat(),
        "valid_until": (today + timedelta(days=365)).isoformat(),
        "next_verification_date": None,
    }

    response = authenticated_client.post(
        "/api/verifications/",
        data=data,
        format="json",
        )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["instrument"] == instrument.pk

    verification = Verification.objects.get(pk=response.data["id"])

    assert verification.instrument == instrument
    assert verification.verification_date == today
    assert verification.valid_until == today + timedelta(days=365)


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("client_fixture", "expected_status", "verification_exists"),
    [
        (
            "authenticated_client",
            status.HTTP_403_FORBIDDEN,
            True,
        ),
        (
            "admin_client",
            status.HTTP_204_NO_CONTENT,
            False,
        ),
    ],
)
def test_verification_delete_permissions(
    request,
    instrument,
    client_fixture,
    expected_status,
    verification_exists,
):
    today = timezone.localdate()

    verification = Verification.objects.create(
        instrument=instrument,
        verification_date=today,
        valid_until=today + timedelta(days=365),
        next_verification_date=None,
    )

    client = request.getfixturevalue(client_fixture)

    response = client.delete(
        f"/api/verifications/{verification.pk}/"
    )

    assert response.status_code == expected_status
    assert (
        Verification.objects.filter(pk=verification.pk).exists()
        is verification_exists
    )