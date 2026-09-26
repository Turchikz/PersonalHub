import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_openapi_schema_is_available():
    client = APIClient()

    response = client.get(reverse("api-schema"))

    assert response.status_code == status.HTTP_200_OK
    assert b"openapi:" in response.content.lower()


@pytest.mark.django_db
def test_swagger_ui_is_available():
    client = APIClient()

    response = client.get(reverse("api-docs"))

    assert response.status_code == status.HTTP_200_OK
    assert b"swagger-ui" in response.content.lower()