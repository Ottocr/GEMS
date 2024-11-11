from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from statistics import mean
from django.db import transaction
from .model_imports import get_risk_type_model, get_asset_model

class BarrierCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_shareable = models.BooleanField(
        default=False,
        help_text="Indicates if barriers in this category can be shared across multiple assets (e.g., IT systems)"
    )

    def __str__(self):
        return self.name

class BarrierCharacteristic(models.Model):
    """Defines specific characteristics that can be assessed for a barrier type"""
    name = models.CharField(max_length=100)
    category = models.ForeignKey(BarrierCategory, on_delete=models.CASCADE, related_name='characteristics')
    description = models.TextField()
    
    # Example: For a fence - height, material, condition
    possible_values = models.JSONField(
        help_text="JSON array of possible values and their effectiveness scores"
    )
    
    weight = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Weight of this characteristic in overall barrier effectiveness (0-1)"
    )

    def __str__(self):
        return f"{self.category.name} - {self.name}"

class Barrier(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(BarrierCategory, on_delete=models.PROTECT)
    performance_adjustment = models.FloatField(default=1.0)
    is_active = models.BooleanField(default=True)
    implementation_date = models.DateField(auto_now_add=True)
    last_assessment_date = models.DateField(auto_now=True)

    def __str__(self):
        return self.name

    @transaction.atomic
    def get_overall_effectiveness_score(self):
        """Calculate overall effectiveness considering characteristics and performance"""
        scores = self.effectiveness_scores.all()
        if not scores:
            return 0
            
        # Get characteristic assessments
        characteristic_scores = self.characteristic_assessments.all()
        characteristic_adjustment = 1.0
        
        if characteristic_scores:
            total_weight = sum(cs.characteristic.weight for cs in characteristic_scores)
            if total_weight > 0:
                weighted_score = sum(
                    cs.score * (cs.characteristic.weight / total_weight)
                    for cs in characteristic_scores
                )
                characteristic_adjustment = weighted_score / 10  # Normalize to 0-1 range

        base_score = mean([score.overall_effectiveness_score for score in scores])
        return round(base_score * self.performance_adjustment * characteristic_adjustment, 2)

    def get_risk_category_effectiveness_score(self, risk_type):
        """Get effectiveness score for a specific risk type"""
        scores = self.effectiveness_scores.filter(risk_type=risk_type)
        if not scores:
            return 0
            
        base_score = mean([score.overall_effectiveness_score for score in scores])
        
        # Apply scenario-specific adjustments
        scenario_scores = self.scenario_effectiveness.filter(
            scenario__risk_subtypes__risk_type=risk_type
        )
        if scenario_scores:
            scenario_adjustment = mean([score.effectiveness_score for score in scenario_scores])
            base_score *= scenario_adjustment

        return round(base_score * self.performance_adjustment, 2)

    def get_effectiveness_scores_by_risk(self):
        """Get effectiveness scores broken down by risk type"""
        return {
            score.risk_type.name: self.get_risk_category_effectiveness_score(score.risk_type)
            for score in self.effectiveness_scores.all()
        }

    @transaction.atomic
    def adjust_performance(self, impact_rating):
        """Adjust barrier performance based on impact rating"""
        impact_adjustments = {
            'NO_IMPACT': 1.0,
            'MINIMAL': 0.95,
            'SUBSTANTIAL': 0.8,
            'MAJOR': 0.6,
            'COMPROMISED': 0.2,
        }
        self.performance_adjustment *= impact_adjustments.get(impact_rating, 1.0)
        self.performance_adjustment = max(0.1, min(self.performance_adjustment, 1.0))
        self.save()

    def update_overall_effectiveness(self):
        """Update overall effectiveness and propagate changes"""
        self.get_overall_effectiveness_score()
        self.save()

    def propagate_effectiveness(self):
        """Propagate effectiveness changes to linked assets"""
        for asset_link in self.asset_links.all():
            for asset in asset_link.assets.all():
                asset.update_risk_assessment_based_on_link()

class BarrierCharacteristicAssessment(models.Model):
    """Assessment of a barrier's specific characteristics"""
    barrier = models.ForeignKey(Barrier, on_delete=models.CASCADE, related_name='characteristic_assessments')
    characteristic = models.ForeignKey(BarrierCharacteristic, on_delete=models.CASCADE)
    selected_value = models.CharField(max_length=100)
    score = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Effectiveness score for this characteristic (1-10)"
    )
    notes = models.TextField(blank=True, null=True)
    assessed_date = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('barrier', 'characteristic')

class BarrierScenarioEffectiveness(models.Model):
    """Effectiveness of a barrier in specific scenarios"""
    barrier = models.ForeignKey(Barrier, on_delete=models.CASCADE, related_name='scenario_effectiveness')
    scenario = models.ForeignKey('Scenario', on_delete=models.CASCADE)
    effectiveness_score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Effectiveness multiplier for this scenario (0-1)"
    )
    assessment_date = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('barrier', 'scenario')

class BarrierEffectivenessScore(models.Model):
    barrier = models.ForeignKey(Barrier, on_delete=models.CASCADE, related_name='effectiveness_scores')
    risk_type = models.ForeignKey('RiskType', on_delete=models.CASCADE, related_name='barrier_effectiveness_scores')
    
    overall_effectiveness_score = models.FloatField(default=0)
    
    preventive_capability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rate the barrier's ability to prevent this specific risk (1-10)"
    )
    detection_capability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rate the barrier's ability to detect this specific risk event (1-10)"
    )
    response_capability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rate the barrier's ability to respond to this specific detected risk (1-10)"
    )
    reliability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rate the barrier's reliability and consistency for this specific risk (1-10)"
    )
    coverage = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Rate how comprehensively the barrier addresses this specific risk (1-10)"
    )

    def __str__(self):
        return f"{self.barrier.name} effectiveness against {self.risk_type.name}"

    def save(self, *args, **kwargs):
        self.overall_effectiveness_score = self.calculate_overall_effectiveness()
        super().save(*args, **kwargs)

    def calculate_overall_effectiveness(self):
        return round(
            self.preventive_capability * 0.30 +
            self.detection_capability * 0.20 +
            self.response_capability * 0.20 +
            self.reliability * 0.15 +
            self.coverage * 0.15,
            2
        )

    class Meta:
        unique_together = ('barrier', 'risk_type')

class BarrierQuestion(models.Model):
    barrier = models.ForeignKey(Barrier, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    risk_type = models.ForeignKey('RiskType', on_delete=models.CASCADE, related_name='barrier_questions')
    scenario = models.ForeignKey('Scenario', on_delete=models.CASCADE, null=True, blank=True)
    answer_choices = models.JSONField(
        help_text='Format: {"answers": [{"choice": "Yes", "impact": 1, "description": "Explanation"}]}'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.barrier.name} - {self.question_text[:50]}"

class BarrierQuestionAnswer(models.Model):
    question = models.ForeignKey(BarrierQuestion, on_delete=models.CASCADE, related_name='answers')
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='barrier_question_answers')
    selected_choice = models.CharField(max_length=255)
    impact = models.IntegerField(validators=[MinValueValidator(-10), MaxValueValidator(10)])
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Answer to {self.question.question_text[:50]} for {self.asset.name}"

    class Meta:
        unique_together = ('question', 'asset')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Trigger risk assessment update
        self.asset.update_risk_assessment()

class BarrierIssueReport(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    IMPACT_CHOICES = [
        ('NO_IMPACT', 'No Impact'),
        ('MINIMAL', 'Minimal Impact'),
        ('SUBSTANTIAL', 'Substantial Impact'),
        ('MAJOR', 'Major Impact'),
        ('COMPROMISED', 'Barrier Completely Compromised'),
    ]

    barrier = models.ForeignKey(Barrier, on_delete=models.CASCADE, related_name='issue_reports')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='reported_barrier_issues')
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    impact_rating = models.CharField(max_length=20, choices=IMPACT_CHOICES, default='NO_IMPACT')
    reported_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(null=True, blank=True)
    affected_assets = models.ManyToManyField('Asset', related_name='barrier_issue_reports', blank=True)

    def __str__(self):
        return f"Issue for {self.barrier.name} - {self.get_status_display()}"

    @transaction.atomic
    def update_risk_matrix(self):
        """Update risk matrices for affected assets"""
        for asset in self.affected_assets.all():
            asset.update_risk_assessment()

def update_risk_assessment(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.update_risk_matrix()

models.signals.m2m_changed.connect(update_risk_assessment, sender=BarrierIssueReport.affected_assets.through)
