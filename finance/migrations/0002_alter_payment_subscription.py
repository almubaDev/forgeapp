# Generated by Django 5.0.2 on 2025-02-28 16:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
        ('forgeapp', '0016_payment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='subscription',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='finance_payments', to='forgeapp.subscription', verbose_name='Suscripción'),
        ),
    ]
