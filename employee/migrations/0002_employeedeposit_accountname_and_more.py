# Generated by Django 5.0.6 on 2024-08-03 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='employeedeposit',
            name='accountname',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='employeedeposit',
            name='accountno',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='employeedeposit',
            name='bankcode',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='employeedeposit',
            name='bankname',
            field=models.CharField(default='', max_length=255, null=True),
        ),
    ]