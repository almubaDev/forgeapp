# Generated by Django 5.0.2 on 2025-02-22 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.CharField(max_length=255)),
                ('reference_id', models.CharField(max_length=255, unique=True)),
                ('status', models.CharField(choices=[('pending', 'Pendiente'), ('approved', 'Aprobado'), ('rejected', 'Rechazado')], default='pending', max_length=20)),
                ('payment_url', models.URLField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
