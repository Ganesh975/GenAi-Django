# Generated by Django 5.0.4 on 2024-06-26 17:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("AIApp", "0006_userdescription_history_list"),
    ]

    operations = [
        migrations.AddField(
            model_name="userdescription",
            name="train_status",
            field=models.BooleanField(default=False),
        ),
    ]
