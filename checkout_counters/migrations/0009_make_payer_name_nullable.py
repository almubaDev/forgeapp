# Generated by Django 5.0.2 on 2025-02-23 01:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout_counters', '0008_paymentlink_subscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlink',
            name='payer_name',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Nombre del Pagador'),
        ),
    ]
