# Generated by Django 5.0.6 on 2024-11-08 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payout', '0011_balancetimeline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payout',
            name='money',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
    ]
