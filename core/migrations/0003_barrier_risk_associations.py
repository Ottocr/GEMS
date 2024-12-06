from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_barrier_characteristics'),
    ]

    operations = [
        migrations.AddField(
            model_name='barrier',
            name='risk_types',
            field=models.ManyToManyField(blank=True, help_text='Risk types this barrier affects. Leave empty if barrier only affects specific subtypes.', related_name='barriers', to='core.risktype'),
        ),
        migrations.AddField(
            model_name='barrier',
            name='risk_subtypes',
            field=models.ManyToManyField(blank=True, help_text='Risk subtypes this barrier affects. Leave empty if barrier affects entire risk types.', related_name='barriers', to='core.risksubtype'),
        ),
        migrations.AddField(
            model_name='barriereffectivenessscore',
            name='risk_subtype',
            field=models.ForeignKey(blank=True, help_text='Specific subtype this score applies to. Leave empty if score applies to entire risk type.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='barrier_effectiveness_scores', to='core.risksubtype'),
        ),
        migrations.AddField(
            model_name='barrierquestion',
            name='risk_subtype',
            field=models.ForeignKey(blank=True, help_text='Specific subtype this question applies to. Leave empty if question applies to entire risk type.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='barrier_questions', to='core.risksubtype'),
        ),
        migrations.AlterUniqueTogether(
            name='barriereffectivenessscore',
            unique_together={('barrier', 'risk_type', 'risk_subtype')},
        ),
    ]
