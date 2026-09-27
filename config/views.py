from django.db import connection
from django.db.utils import DatabaseError
from django.http import HttpRequest, JsonResponse


def health_check(request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse(
            {
                "status": "unhealthy",
                "database": "unavaliable",
            },
            status=503,
        )

    return JsonResponse(
        {
            "status": "ok",
            "database": "avaliable"
        }
    )