from django.db import migrations, models
from django.db.models import F

def generate_reference_ids(apps, schema_editor):
    Subscription = apps.get_model('forgeapp', 'Subscription')
    
    # Contador para cada tipo
    annual_count = 1
    monthly_count = 1
    
    # Actualizar suscripciones anuales
    annual_subs = Subscription.objects.filter(payment_type='annual')
    for sub in annual_subs:
        sub.reference_id = f'AN{annual_count:06d}'
        sub.save()
        annual_count += 1
    
    # Actualizar suscripciones mensuales
    monthly_subs = Subscription.objects.filter(payment_type='monthly')
    for sub in monthly_subs:
        sub.reference_id = f'ME{monthly_count:06d}'
        sub.save()
        monthly_count += 1

class Migration(migrations.Migration):

    dependencies = [
        ('forgeapp', '0001_initial'),
    ]

    operations = [
        # Paso 1: Agregar el campo sin unique=True
        migrations.AddField(
            model_name='subscription',
            name='reference_id',
            field=models.CharField(
                'ID de Referencia',
                max_length=20,
                default='TEMP000000'
            ),
        ),
        
        # Paso 2: Ejecutar la función para generar IDs únicos
        migrations.RunPython(
            generate_reference_ids,
            reverse_code=migrations.RunPython.noop
        ),
        
        # Paso 3: Hacer el campo único
        migrations.AlterField(
            model_name='subscription',
            name='reference_id',
            field=models.CharField(
                'ID de Referencia',
                max_length=20,
                unique=True,
                default='TEMP000000'
            ),
        ),
    ]
