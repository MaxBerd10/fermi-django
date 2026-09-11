from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("departments", "0003_staffmember_email_staffmember_faculty_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="staffmember",
            name="full_name",
        ),
        migrations.AddField(
            model_name="staffmember",
            name="full_name_uz",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="staffmember",
            name="full_name_ru",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="staffmember",
            name="full_name_en",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
