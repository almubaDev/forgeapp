# Generated by Django 5.0.2 on 2025-02-22 01:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout_counters', '0004_paymentlink_reference_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlink',
            name='reference_id',
            field=models.CharField(max_length=100, unique=True),
        ),
    ]
