from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.DeleteModel(
            name='BarrierCharacteristicAssessment',
        ),
        migrations.DeleteModel(
            name='BarrierCharacteristic',
        ),
    ]
