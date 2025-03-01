# Generated by Django 5.0.2 on 2025-02-23 00:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout_counters', '0007_alter_paymentlink_options_and_more'),
        ('forgeapp', '0011_rename_subscription_calculator'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentlink',
            name='subscription',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payment_links', to='forgeapp.subscription', verbose_name='Suscripción'),
        ),
    ]
