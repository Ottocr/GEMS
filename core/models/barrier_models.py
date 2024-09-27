from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from statistics import mean
from .model_imports import get_risk_type_model, get_asset_model

class BarrierCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Barrier(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey(BarrierCategory, on_delete=models.PROTECT)
    performance_adjustment = models.FloatField(default=1.0)

    def __str__(self):
        return self.name

    def get_overall_effectiveness_score(self):
        scores = self.effectiveness_scores.all()
        if not scores:
            return 0
        return round(mean([score.overall_effectiveness_score for score in scores]) * self.performance_adjustment, 2)

    def get_risk_category_effectiveness_score(self, risk_type):
        scores = self.effectiveness_scores.filter(risk_type=risk_type)
        if not scores:
            return 0
        return round(mean([score.overall_effectiveness_score for score in scores]) * self.performance_adjustment, 2)

    def get_effectiveness_scores_by_risk(self):
        return {
            score.risk_type.name: round(score.overall_effectiveness_score * self.performance_adjustment, 2)
            for score in self.effectiveness_scores.all()
        }

    def adjust_performance(self, impact_rating):
        impact_adjustments = {
            'NO_IMPACT': 1.0,
            'MINIMAL': 0.95,
            'SUBSTANTIAL': 0.8,
            'MAJOR': 0.6,
            'COMPROMISED': 0.2,
        }
        self.performance_adjustment *= impact_adjustments.get(impact_rating, 1.0)
        self.performance_adjustment = max(0.1, min(self.performance_adjustment, 1.0))  # Ensure it's between 0.1 and 1.0
        self.save()

    def update_overall_effectiveness(self):
        self.get_overall_effectiveness_score()  # This method already uses performance_adjustment
        self.save()

    def propagate_effectiveness(self):
        for asset_link in self.asset_links.all():
            for asset in asset_link.assets.all():
                asset.update_risk_assessment_based_on_link()

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
    answer_choices = models.JSONField()  # Format like {"answers": [{"choice": "Yes", "impact": 1}, {"choice": "No", "impact": -1}]}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.barrier.name} - {self.question_text[:50]}"

class BarrierQuestionAnswer(models.Model):
    question = models.ForeignKey(BarrierQuestion, on_delete=models.CASCADE, related_name='answers')
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='barrier_question_answers')
    selected_choice = models.CharField(max_length=255)
    impact = models.IntegerField(validators=[MinValueValidator(-10), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Answer to {self.question.question_text[:50]} for {self.asset.name}"

    class Meta:
        unique_together = ('question', 'asset')

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

    def update_risk_matrix(self):
        # Update risk matrix only for affected assets
        for asset in self.affected_assets.all():
            asset.update_risk_assessment()

def update_risk_assessment(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.update_risk_matrix()

models.signals.m2m_changed.connect(update_risk_assessment, sender=BarrierIssueReport.affected_assets.through)