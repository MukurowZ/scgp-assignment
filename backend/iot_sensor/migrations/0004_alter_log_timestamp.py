# Generated by Django 5.1.6 on 2025-03-03 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iot_sensor', '0003_rename_timestamps_log_timestamp'),
    ]

    operations = [
        migrations.AlterField(
            model_name='log',
            name='timestamp',
            field=models.DateTimeField(db_index=True, unique=True),
        ),
    ]
