# Generated by Django 5.0.4 on 2024-06-26 15:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("AIApp", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="userdescription",
            name="url_data",
            field=models.JSONField(default=list),
        ),
    ]
