# Generated by Django 5.0.6 on 2024-07-11 22:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payout', '0005_payout_updated_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payout',
            name='status',
            field=models.BooleanField(default=False, null=True),
        ),
    ]