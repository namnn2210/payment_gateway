# Generated by Django 5.0.6 on 2024-09-17 09:21

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0024_alter_employeeworkingsession_start_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employeeworkingsession',
            name='start_time',
            field=models.DateTimeField(default=datetime.datetime(2024, 9, 17, 9, 21, 41, 354901)),
        ),
    ]
