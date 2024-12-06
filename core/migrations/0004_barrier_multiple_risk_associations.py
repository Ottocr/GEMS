from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_barrier_risk_associations'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='barrierquestion',
            name='risk_type',
        ),
        migrations.RemoveField(
            model_name='barrierquestion',
            name='risk_subtype',
        ),
        migrations.AddField(
            model_name='barrierquestion',
            name='risk_types',
            field=models.ManyToManyField(
                help_text='Risk types this question applies to. Can select multiple types.',
                related_name='barrier_questions',
                to='core.risktype'
            ),
        ),
        migrations.AddField(
            model_name='barrierquestion',
            name='risk_subtypes',
            field=models.ManyToManyField(
                blank=True,
                help_text='Risk subtypes this question applies to. Can select multiple subtypes.',
                related_name='barrier_questions',
                to='core.risksubtype'
            ),
        ),
        migrations.AlterField(
            model_name='barrier',
            name='risk_types',
            field=models.ManyToManyField(
                blank=True,
                help_text='Risk types this barrier affects. Can select multiple types.',
                related_name='barriers',
                to='core.risktype'
            ),
        ),
        migrations.AlterField(
            model_name='barrier',
            name='risk_subtypes',
            field=models.ManyToManyField(
                blank=True,
                help_text='Risk subtypes this barrier affects. Can select multiple subtypes.',
                related_name='barriers',
                to='core.risksubtype'
            ),
        ),
    ]
