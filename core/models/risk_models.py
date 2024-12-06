from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from statistics import mean
from .model_imports import get_country_model, get_asset_model, get_barrier_model

class RiskType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class RiskSubtype(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    risk_type = models.ForeignKey(RiskType, on_delete=models.CASCADE, related_name='subtypes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.risk_type.name} - {self.name}"

    class Meta:
        unique_together = ('name', 'risk_type')

class Scenario(models.Model):
    """
    A scenario represents a specific risk event (e.g., terrorist attack, cyber breach).
    Each scenario has associated questions that help assess its likelihood and impact.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    risk_subtypes = models.ManyToManyField(RiskSubtype, related_name='scenarios')
    barriers = models.ManyToManyField('Barrier', related_name='scenarios', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_risk_score_for_asset(self, asset):
        """Calculate risk score for this scenario based on asset's answers."""
        answers = self.asset_answers.filter(asset=asset)
        if not answers.exists():
            return None
        return mean([answer.selected_choice.score for answer in answers])

    def get_applicable_barriers(self):
        """Get all barriers that apply to this scenario's risk types and subtypes"""
        risk_types = RiskType.objects.filter(subtypes__in=self.risk_subtypes.all()).distinct()
        
        # Get barriers that directly affect the risk types
        type_barriers = self.barriers.filter(risk_types__in=risk_types)
        
        # Get barriers that affect specific subtypes
        subtype_barriers = self.barriers.filter(risk_subtypes__in=self.risk_subtypes.all())
        
        return (type_barriers | subtype_barriers).distinct()

class ScenarioQuestion(models.Model):
    """
    Questions associated with a scenario to assess its likelihood and impact.
    Each question has multiple choices with associated risk scores.
    """
    QUESTION_TYPES = [
        ('LIKELIHOOD', 'Likelihood Assessment'),
        ('IMPACT', 'Impact Assessment'),
        ('VULNERABILITY', 'Vulnerability Assessment'),
    ]

    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=500)
    description = models.TextField(null=True, blank=True)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    weight = models.FloatField(default=1.0, validators=[MinValueValidator(0.1), MaxValueValidator(10.0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.scenario.name} - {self.text}"

class QuestionChoice(models.Model):
    """
    Multiple choice options for scenario questions.
    Each choice has an associated risk score.
    """
    question = models.ForeignKey(ScenarioQuestion, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200)
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.question.text} - {self.text} (Score: {self.score})"

    class Meta:
        ordering = ['score']

class AssetScenarioAnswer(models.Model):
    """
    Stores answers to scenario questions per asset.
    These answers are used to calculate risk scores for the asset.
    """
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='scenario_answers')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='asset_answers')
    question = models.ForeignKey(ScenarioQuestion, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(QuestionChoice, on_delete=models.CASCADE)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset.name} - {self.scenario.name} - {self.question.text}"

    class Meta:
        unique_together = ('asset', 'scenario', 'question')

class RiskScenarioAssessment(models.Model):
    """
    Overall risk assessment for a scenario-asset combination.
    Calculated based on answers to scenario questions and barrier effectiveness.
    """
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='risk_scenario_assessments')
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='assessments')
    residual_risk_score = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    likelihood_score = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    impact_score = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    vulnerability_score = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    barrier_effectiveness = models.JSONField(null=True, blank=True)
    assessment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset.name} - {self.scenario.name}"

    class Meta:
        unique_together = ('asset', 'scenario', 'assessment_date')

    def calculate_scores(self):
        """Calculate likelihood, impact, and vulnerability scores from answers."""
        answers = AssetScenarioAnswer.objects.filter(asset=self.asset, scenario=self.scenario)
        
        likelihood_answers = answers.filter(question__question_type='LIKELIHOOD')
        impact_answers = answers.filter(question__question_type='IMPACT')
        vulnerability_answers = answers.filter(question__question_type='VULNERABILITY')
        
        self.likelihood_score = self._calculate_weighted_score(likelihood_answers)
        self.impact_score = self._calculate_weighted_score(impact_answers)
        self.vulnerability_score = self._calculate_weighted_score(vulnerability_answers)
        
        # Calculate residual risk score considering barrier effectiveness
        base_risk = (self.likelihood_score * self.impact_score * self.vulnerability_score) ** (1/3)
        
        # Get all applicable barriers and their effectiveness
        self.barrier_effectiveness = self._calculate_barrier_effectiveness()
        
        if self.barrier_effectiveness:
            avg_barrier_effectiveness = mean(self.barrier_effectiveness.values())
            self.residual_risk_score = base_risk / (1 + avg_barrier_effectiveness)
        else:
            self.residual_risk_score = base_risk

    def _calculate_weighted_score(self, answers):
        """Calculate weighted average score for a set of answers."""
        if not answers.exists():
            return 5  # Default middle score
            
        total_weight = sum(answer.question.weight for answer in answers)
        weighted_sum = sum(
            answer.selected_choice.score * answer.question.weight 
            for answer in answers
        )
        return round(weighted_sum / total_weight, 2)

    def _calculate_barrier_effectiveness(self):
        """Calculate barrier effectiveness considering both risk type and subtype levels"""
        effectiveness = {}
        
        # Get all applicable barriers
        applicable_barriers = self.scenario.get_applicable_barriers()
        
        for barrier in applicable_barriers:
            barrier_score = 0
            
            # Check risk type level effectiveness
            for risk_type in self.scenario.risk_subtypes.values_list('risk_type', flat=True).distinct():
                if barrier.risk_types.filter(id=risk_type).exists():
                    type_score = barrier.get_risk_category_effectiveness_score(risk_type)
                    barrier_score = max(barrier_score, type_score)
            
            # Check risk subtype level effectiveness
            for subtype in self.scenario.risk_subtypes.all():
                if barrier.risk_subtypes.filter(id=subtype.id).exists():
                    subtype_score = barrier.get_risk_category_effectiveness_score(subtype.risk_type)
                    barrier_score = max(barrier_score, subtype_score)
            
            if barrier_score > 0:
                effectiveness[str(barrier.id)] = barrier_score
        
        return effectiveness

    def save(self, *args, **kwargs):
        self.calculate_scores()
        super().save(*args, **kwargs)

class BaselineThreatAssessment(models.Model):
    risk_type = models.ForeignKey(RiskType, on_delete=models.CASCADE, related_name='baseline_threats')
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='baseline_threats')
    baseline_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=5)
    date_assessed = models.DateField(default=timezone.now)
    impact_on_assets = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.country.name} - {self.risk_type.name} - {self.baseline_score}"

    class Meta:
        unique_together = ('risk_type', 'country', 'date_assessed')

class FinalRiskMatrix(models.Model):
    RISK_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='risk_matrices')
    risk_type = models.ForeignKey(RiskType, on_delete=models.CASCADE, related_name='risk_matrices')
    residual_risk_score = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    risk_level = models.CharField(max_length=20, choices=RISK_LEVELS)
    sub_risk_details = models.JSONField(null=True, blank=True)
    barrier_details = models.JSONField(null=True, blank=True)
    date_generated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.name} - {self.risk_type.name} - {self.risk_level}"

    class Meta:
        unique_together = ('asset', 'risk_type', 'date_generated')

    @classmethod
    def generate_matrices(cls, asset):
        """Generate risk matrices for an asset based on scenario assessments."""
        risk_types = RiskType.objects.filter(
            subtypes__scenarios__assessments__asset=asset
        ).distinct()
        
        for risk_type in risk_types:
            # Get all scenario assessments for this risk type
            assessments = RiskScenarioAssessment.objects.filter(
                asset=asset,
                scenario__risk_subtypes__risk_type=risk_type
            )
            
            if assessments.exists():
                # Calculate average residual risk score
                avg_residual_risk = mean([a.residual_risk_score for a in assessments])
                
                # Get BTA score if available
                bta = BaselineThreatAssessment.objects.filter(
                    risk_type=risk_type,
                    country=asset.country
                ).order_by('-date_assessed').first()
                
                if bta:
                    # Combine scenario-based risk with BTA
                    final_score = (avg_residual_risk + bta.baseline_score) / 2
                else:
                    final_score = avg_residual_risk
                
                # Create or update risk matrix
                cls.objects.update_or_create(
                    asset=asset,
                    risk_type=risk_type,
                    defaults={
                        'residual_risk_score': final_score,
                        'risk_level': cls.calculate_risk_level(final_score),
                        'sub_risk_details': {
                            'scenario_assessments': [
                                {
                                    'scenario': a.scenario.name,
                                    'likelihood': a.likelihood_score,
                                    'impact': a.impact_score,
                                    'vulnerability': a.vulnerability_score,
                                    'residual_risk': a.residual_risk_score,
                                } for a in assessments
                            ],
                            'bta_score': bta.baseline_score if bta else None
                        },
                        'barrier_details': {
                            barrier.name: barrier.get_risk_category_effectiveness_score(risk_type)
                            for barrier in asset.barriers.all()
                        }
                    }
                )

    @staticmethod
    def calculate_risk_level(score):
        if score <= 3:
            return 'LOW'
        elif score <= 5:
            return 'MEDIUM'
        elif score <= 8:
            return 'HIGH'
        else:
            return 'CRITICAL'
