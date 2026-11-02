from django.db import migrations, models


def number_existing_applications(apps, schema_editor):
    """Gives the applications already received their number within their contest, oldest first."""
    ContestSubmission = apps.get_model("forms", "ContestSubmission")
    counters = {}
    for row in ContestSubmission.objects.filter(contest__isnull=False).order_by("created_at", "id"):
        counters[row.contest_id] = counters.get(row.contest_id, 0) + 1
        ContestSubmission.objects.filter(pk=row.pk).update(number=counters[row.contest_id])


class Migration(migrations.Migration):

    dependencies = [
        ("forms", "0002_contestsubmission"),
    ]

    operations = [
        migrations.AddField(
            model_name="contestsubmission",
            name="number",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(number_existing_applications, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="contestsubmission",
            constraint=models.UniqueConstraint(fields=("contest", "number"), name="contest_submission_number_unique"),
        ),
    ]
