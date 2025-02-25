from django.db import migrations, models

def update_pending_to_inactive(apps, schema_editor):
    Subscription = apps.get_model('forgeapp', 'Subscription')
    Subscription.objects.filter(status='pending').update(status='inactive')

class Migration(migrations.Migration):

    dependencies = [
        ('forgeapp', '0002_add_subscription_reference_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='status',
            field=models.CharField(choices=[('active', 'Activa'), ('inactive', 'Inactiva'), ('cancelled', 'Cancelada'), ('pending', 'Pendiente'), ('expired', 'Expirada')], default='inactive', max_length=20, verbose_name='Estado'),
        ),
        migrations.RunPython(update_pending_to_inactive),
    ]
