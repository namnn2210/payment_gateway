# Generated by Django 5.0.6 on 2024-09-08 14:30

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0003_employeeworkingsession'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeeworkingsession',
            name='start_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 8, 21, 29, 54, 979101)),
        ),
    ]