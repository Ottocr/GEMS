# Generated by Django 5.1.1 on 2024-10-30 23:49

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetCriticalityQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('choice1', models.CharField(max_length=255)),
                ('score1', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice2', models.CharField(max_length=255)),
                ('score2', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice3', models.CharField(max_length=255)),
                ('score3', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice4', models.CharField(max_length=255)),
                ('score4', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice5', models.CharField(max_length=255)),
                ('score5', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssetType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Barrier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('performance_adjustment', models.FloatField(default=1.0)),
                ('is_active', models.BooleanField(default=True)),
                ('implementation_date', models.DateField(auto_now_add=True)),
                ('last_assessment_date', models.DateField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='BarrierCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_shareable', models.BooleanField(default=False, help_text='Indicates if barriers in this category can be shared across multiple assets (e.g., IT systems)')),
            ],
        ),
        migrations.CreateModel(
            name='Continent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='RiskType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('criticality_score', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('vulnerability_score', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='core.assettype')),
                ('barriers', models.ManyToManyField(related_name='assets', to='core.barrier')),
            ],
        ),
        migrations.AddField(
            model_name='barrier',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.barriercategory'),
        ),
        migrations.CreateModel(
            name='BarrierCharacteristic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('possible_values', models.JSONField(help_text='JSON array of possible values and their effectiveness scores')),
                ('weight', models.FloatField(help_text='Weight of this characteristic in overall barrier effectiveness (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='characteristics', to='core.barriercategory')),
            ],
        ),
        migrations.CreateModel(
            name='BarrierIssueReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('IN_PROGRESS', 'In Progress'), ('RESOLVED', 'Resolved'), ('CLOSED', 'Closed')], default='OPEN', max_length=20)),
                ('impact_rating', models.CharField(choices=[('NO_IMPACT', 'No Impact'), ('MINIMAL', 'Minimal Impact'), ('SUBSTANTIAL', 'Substantial Impact'), ('MAJOR', 'Major Impact'), ('COMPROMISED', 'Barrier Completely Compromised')], default='NO_IMPACT', max_length=20)),
                ('reported_at', models.DateTimeField(auto_now_add=True)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('resolution_notes', models.TextField(blank=True, null=True)),
                ('affected_assets', models.ManyToManyField(blank=True, related_name='barrier_issue_reports', to='core.asset')),
                ('barrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issue_reports', to='core.barrier')),
                ('reported_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reported_barrier_issues', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('code', models.CharField(blank=True, max_length=3, null=True)),
                ('geo_data', models.JSONField(blank=True, null=True)),
                ('company_operated', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('continent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='countries', to='core.continent')),
            ],
            options={
                'verbose_name_plural': 'Countries',
            },
        ),
        migrations.AddField(
            model_name='asset',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='core.country'),
        ),
        migrations.CreateModel(
            name='RiskSubtype',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('risk_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subtypes', to='core.risktype')),
            ],
            options={
                'unique_together': {('name', 'risk_type')},
            },
        ),
        migrations.CreateModel(
            name='RiskLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bta_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('vulnerability_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('criticality_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('residual_risk_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_logs', to='core.asset')),
                ('risk_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_logs', to='core.risktype')),
            ],
        ),
        migrations.CreateModel(
            name='AssetVulnerabilityQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('choice1', models.CharField(max_length=255)),
                ('score1', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice2', models.CharField(max_length=255)),
                ('score2', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice3', models.CharField(max_length=255)),
                ('score3', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice4', models.CharField(max_length=255)),
                ('score4', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('choice5', models.CharField(max_length=255)),
                ('score5', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('risk_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vulnerability_questions', to='core.risktype')),
            ],
        ),
        migrations.CreateModel(
            name='AssetLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assets', models.ManyToManyField(related_name='asset_links', to='core.asset')),
                ('shared_barriers', models.ManyToManyField(related_name='asset_links', to='core.barrier')),
                ('shared_risks', models.ManyToManyField(related_name='asset_links', to='core.risktype')),
            ],
        ),
        migrations.CreateModel(
            name='Scenario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assets', models.ManyToManyField(blank=True, related_name='risk_scenarios', to='core.asset')),
                ('barriers', models.ManyToManyField(blank=True, related_name='scenarios', to='core.barrier')),
                ('risk_subtypes', models.ManyToManyField(related_name='scenarios', to='core.risksubtype')),
            ],
        ),
        migrations.CreateModel(
            name='BarrierQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_text', models.TextField()),
                ('answer_choices', models.JSONField(help_text='Format: {"answers": [{"choice": "Yes", "impact": 1, "description": "Explanation"}]}')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('barrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='core.barrier')),
                ('risk_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='barrier_questions', to='core.risktype')),
                ('scenario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.scenario')),
            ],
        ),
        migrations.AddField(
            model_name='asset',
            name='scenarios',
            field=models.ManyToManyField(blank=True, related_name='risk_scenarios', to='core.scenario'),
        ),
        migrations.CreateModel(
            name='AssetCriticalityAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_choice', models.CharField(blank=True, max_length=255, null=True)),
                ('selected_score', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset_criticality_answers', to='core.asset')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='core.assetcriticalityquestion')),
            ],
            options={
                'unique_together': {('asset', 'question')},
            },
        ),
        migrations.CreateModel(
            name='AssetVulnerabilityAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_choice', models.CharField(blank=True, max_length=255, null=True)),
                ('selected_score', models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset_vulnerability_answers', to='core.asset')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='core.assetvulnerabilityquestion')),
            ],
            options={
                'unique_together': {('asset', 'question')},
            },
        ),
        migrations.CreateModel(
            name='BarrierCharacteristicAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_value', models.CharField(max_length=100)),
                ('score', models.IntegerField(help_text='Effectiveness score for this characteristic (1-10)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('notes', models.TextField(blank=True, null=True)),
                ('assessed_date', models.DateTimeField(auto_now=True)),
                ('barrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='characteristic_assessments', to='core.barrier')),
                ('characteristic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.barriercharacteristic')),
            ],
            options={
                'unique_together': {('barrier', 'characteristic')},
            },
        ),
        migrations.CreateModel(
            name='BarrierQuestionAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_choice', models.CharField(max_length=255)),
                ('impact', models.IntegerField(validators=[django.core.validators.MinValueValidator(-10), django.core.validators.MaxValueValidator(10)])),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='barrier_question_answers', to='core.asset')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='answers', to='core.barrierquestion')),
            ],
            options={
                'unique_together': {('question', 'asset')},
            },
        ),
        migrations.CreateModel(
            name='FinalRiskMatrix',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('residual_risk_score', models.FloatField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('risk_level', models.CharField(choices=[('LOW', 'Low'), ('MEDIUM', 'Medium'), ('HIGH', 'High'), ('CRITICAL', 'Critical')], max_length=20)),
                ('sub_risk_details', models.JSONField(blank=True, null=True)),
                ('barrier_details', models.JSONField(blank=True, null=True)),
                ('date_generated', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_matrices', to='core.asset')),
                ('risk_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_matrices', to='core.risktype')),
            ],
            options={
                'unique_together': {('asset', 'risk_type', 'date_generated')},
            },
        ),
        migrations.CreateModel(
            name='BaselineThreatAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('baseline_score', models.IntegerField(default=5, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('date_assessed', models.DateField(default=django.utils.timezone.now)),
                ('impact_on_assets', models.BooleanField(default=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='baseline_threats', to='core.country')),
                ('risk_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='baseline_threats', to='core.risktype')),
            ],
            options={
                'unique_together': {('risk_type', 'country', 'date_assessed')},
            },
        ),
        migrations.CreateModel(
            name='BarrierEffectivenessScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('overall_effectiveness_score', models.FloatField(default=0)),
                ('preventive_capability', models.IntegerField(help_text="Rate the barrier's ability to prevent this specific risk (1-10)", validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('detection_capability', models.IntegerField(help_text="Rate the barrier's ability to detect this specific risk event (1-10)", validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('response_capability', models.IntegerField(help_text="Rate the barrier's ability to respond to this specific detected risk (1-10)", validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('reliability', models.IntegerField(help_text="Rate the barrier's reliability and consistency for this specific risk (1-10)", validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('coverage', models.IntegerField(help_text='Rate how comprehensively the barrier addresses this specific risk (1-10)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('barrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='effectiveness_scores', to='core.barrier')),
                ('risk_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='barrier_effectiveness_scores', to='core.risktype')),
            ],
            options={
                'unique_together': {('barrier', 'risk_type')},
            },
        ),
        migrations.CreateModel(
            name='RiskScenarioAssessment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('residual_risk_score', models.IntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('likelihood_rating', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('barrier_effectiveness', models.JSONField(blank=True, null=True)),
                ('barrier_performance', models.JSONField(blank=True, null=True)),
                ('impact_score', models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(10)])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='risk_scenario_assessments', to='core.asset')),
                ('risk_scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assessments', to='core.scenario')),
            ],
            options={
                'unique_together': {('asset', 'risk_scenario')},
            },
        ),
        migrations.CreateModel(
            name='BarrierScenarioEffectiveness',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('effectiveness_score', models.FloatField(help_text='Effectiveness multiplier for this scenario (0-1)', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1)])),
                ('assessment_date', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('barrier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scenario_effectiveness', to='core.barrier')),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.scenario')),
            ],
            options={
                'unique_together': {('barrier', 'scenario')},
            },
        ),
    ]
