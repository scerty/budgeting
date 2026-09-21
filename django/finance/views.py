from django.db import connection
from django.http import JsonResponse

from .models import Branch, Department, Expense


def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        database_ok = cursor.fetchone()[0] == 1

    return JsonResponse(
        {
            "status": "ok",
            "database": "postgresql" if database_ok else "unknown",
            "branches": Branch.objects.count(),
            "departments": Department.objects.count(),
            "expenses": Expense.objects.count(),
        }
    )
