from unittest.mock import patch

import pytest
from django.db.utils import DatabaseError
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_health_check_returns_200_when_database_is_avaliable():
    client = Client()

    response = client.get(reverse("health-check"))

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "database": "avaliable",
    }

@pytest.mark.django_db
def test_health_check_returns_503_when_database_is_unavaliable():
    client = Client()

    with patch(
        "config.views.connection.cursor",
        side_effect=DatabaseError("Database is unavailable"),
    ):
        response = client.get(reverse("health-check"))

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "database": "unavaliable",
    }