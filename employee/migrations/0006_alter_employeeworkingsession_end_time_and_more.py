# Generated by Django 5.0.6 on 2024-09-12 07:17

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0005_alter_employeeworkingsession_start_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeeworkingsession',
            name='end_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='employeeworkingsession',
            name='start_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 12, 14, 17, 32, 538885)),
        ),
    ]