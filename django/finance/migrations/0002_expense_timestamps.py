from django.db import migrations, models
from django.utils import timezone


def backfill_timestamps(apps, schema_editor):
    expense_model = apps.get_model("finance", "Expense")
    timestamp = timezone.now()
    expense_model.objects.filter(created_at__isnull=True).update(created_at=timestamp)
    expense_model.objects.filter(updated_at__isnull=True).update(updated_at=timestamp)


class Migration(migrations.Migration):
    dependencies = [
        ("finance", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="expense",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name="expense",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.RunPython(backfill_timestamps, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="expense",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name="expense",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
