# Generated by Django 4.2.19 on 2025-02-22 02:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('checkout_counters', '0005_alter_paymentlink_reference_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentlink',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Monto'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='description',
            field=models.CharField(max_length=255, verbose_name='Descripción'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de Expiración'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='is_paid',
            field=models.BooleanField(default=False, verbose_name='Está Pagado'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='payer_email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email del Pagador'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='payer_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nombre del Pagador'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='payment_link',
            field=models.URLField(blank=True, verbose_name='Link de Pago'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='reference_id',
            field=models.CharField(max_length=100, unique=True, verbose_name='ID de Referencia'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='status',
            field=models.CharField(choices=[('pending', 'Pendiente'), ('paid', 'Pagado'), ('expired', 'Expirado'), ('cancelled', 'Cancelado')], default='pending', max_length=20, verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='paymentlink',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización'),
        ),
    ]
