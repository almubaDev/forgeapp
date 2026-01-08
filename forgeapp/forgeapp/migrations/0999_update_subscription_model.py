# Generated migration for subscription model update

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forgeapp', '0012_alter_subscription_reference_id'),  # Ajusta según tu última migración
    ]

    operations = [
        # Remover campo end_date
        migrations.RemoveField(
            model_name='subscription',
            name='end_date',
        ),
        # Agregar campo cancelled_at
        migrations.AddField(
            model_name='subscription',
            name='cancelled_at',
            field=models.DateField(blank=True, null=True, verbose_name='Fecha de Cancelación'),
        ),
        # Cambiar default de auto_renewal a True
        migrations.AlterField(
            model_name='subscription',
            name='auto_renewal',
            field=models.BooleanField(default=True, verbose_name='Autorenovación'),
        ),
    ]
