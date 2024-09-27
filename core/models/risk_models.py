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
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    risk_subtypes = models.ManyToManyField(RiskSubtype, related_name='scenarios')
    assets = models.ManyToManyField('Asset', related_name='risk_scenarios', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    barriers = models.ManyToManyField('Barrier', related_name='scenarios', blank=True)

    def __str__(self):
        return self.name

class RiskScenarioAssessment(models.Model):
    asset = models.ForeignKey('Asset', on_delete=models.CASCADE, related_name='risk_scenario_assessments')
    risk_scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name='assessments')
    residual_risk_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    likelihood_rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    barrier_effectiveness = models.JSONField(null=True, blank=True)
    barrier_performance = models.JSONField(null=True, blank=True)
    impact_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset.name} - {self.risk_scenario.name}"

    class Meta:
        unique_together = ('asset', 'risk_scenario')

    def calculate_residual_risk_score(self):
        if not self.barrier_effectiveness:
            return self.likelihood_rating * self.impact_score
    
        avg_barrier_effectiveness = mean(self.barrier_effectiveness.values())
        return round((self.likelihood_rating * self.impact_score) / (1 + avg_barrier_effectiveness), 2)

    def save(self, *args, **kwargs):
        self.residual_risk_score = self.calculate_residual_risk_score()
        super().save(*args, **kwargs)

    def calculate_barrier_effectiveness(self):
        if not self.barrier_performance:
            self.barrier_effectiveness = {}
        else:
            effectiveness_scores = []
            for barrier_id, performance in self.barrier_performance.items():
                barrier = Barrier.objects.get(id=barrier_id)
                effectiveness = barrier.get_overall_effectiveness_score() * performance
                effectiveness_scores.append(effectiveness)
                self.barrier_effectiveness[barrier_id] = effectiveness
            # Update residual risk score based on barrier effectiveness
            self.residual_risk_score = self.calculate_residual_risk_score()

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
        risk_types = RiskType.objects.filter(subtypes__scenarios__assets=asset).distinct()
        
        for risk_type in risk_types:
            # Calculate overall risk matrix
            cls.generate_overall_matrix(asset, risk_type)
            
            # Calculate risk-specific matrices
            cls.generate_risk_specific_matrices(asset, risk_type)
            
            # Calculate barrier-specific matrices
            cls.generate_barrier_specific_matrices(asset, risk_type)

    @classmethod
    def generate_overall_matrix(cls, asset, risk_type):
        assessments = RiskScenarioAssessment.objects.filter(
            asset=asset,
            risk_scenario__risk_subtypes__risk_type=risk_type
        )
        
        if assessments:
            avg_residual_risk = mean([assessment.residual_risk_score for assessment in assessments])
            bta = BaselineThreatAssessment.objects.filter(
                risk_type=risk_type,
                country=asset.country
            ).order_by('-date_assessed').first()
            
            if bta:
                residual_risk_score = round((avg_residual_risk + bta.baseline_score) / 2, 2)
            else:
                residual_risk_score = round(avg_residual_risk, 2)
            
            residual_risk_score = round((residual_risk_score + asset.vulnerability_score + asset.criticality_score) / 3, 2)
            
            risk_level = cls.calculate_risk_level(residual_risk_score)
            
            cls.objects.update_or_create(
                asset=asset,
                risk_type=risk_type,
                defaults={
                    'residual_risk_score': residual_risk_score,
                    'risk_level': risk_level,
                    'sub_risk_details': [
                        {
                            'scenario': assessment.risk_scenario.name,
                            'residual_risk_score': assessment.residual_risk_score,
                            'likelihood_rating': assessment.likelihood_rating,
                            'impact_score': assessment.impact_score,
                        } for assessment in assessments
                    ],
                    'barrier_details': {
                        barrier.name: barrier.get_risk_category_effectiveness_score(risk_type)
                        for barrier in get_barrier_model().objects.filter(effectiveness_scores__risk_type=risk_type)
                    }
                }
            )

    @classmethod
    def generate_risk_specific_matrices(cls, asset, risk_type):
        for subtype in risk_type.subtypes.all():
            assessments = RiskScenarioAssessment.objects.filter(
                asset=asset,
                risk_scenario__risk_subtypes=subtype
            )
            
            if assessments:
                avg_residual_risk = mean([assessment.residual_risk_score for assessment in assessments])
                risk_level = cls.calculate_risk_level(avg_residual_risk)
                
                cls.objects.update_or_create(
                    asset=asset,
                    risk_type=subtype,
                    defaults={
                        'residual_risk_score': avg_residual_risk,
                        'risk_level': risk_level,
                        'sub_risk_details': [
                            {
                                'scenario': assessment.risk_scenario.name,
                                'residual_risk_score': assessment.residual_risk_score,
                                'likelihood_rating': assessment.likelihood_rating,
                                'impact_score': assessment.impact_score,
                            } for assessment in assessments
                        ],
                        'barrier_details': {
                            barrier.name: barrier.get_effectiveness_scores_by_risk()[subtype.name]
                            for barrier in get_barrier_model().objects.filter(effectiveness_scores__risk_type=subtype)
                        }
                    }
                )

    @classmethod
    def generate_barrier_specific_matrices(cls, asset, risk_type):
        barriers = get_barrier_model().objects.filter(effectiveness_scores__risk_type=risk_type)
        
        for barrier in barriers:
            effectiveness_score = barrier.get_risk_category_effectiveness_score(risk_type)
            risk_level = cls.calculate_risk_level(10 - effectiveness_score)  # Invert score for risk level
            
            cls.objects.update_or_create(
                asset=asset,
                risk_type=barrier,
                defaults={
                    'residual_risk_score': 10 - effectiveness_score,  # Invert score for residual risk
                    'risk_level': risk_level,
                    'sub_risk_details': None,
                    'barrier_details': {
                        'overall_effectiveness': effectiveness_score,
                        'risk_specific_effectiveness': barrier.get_effectiveness_scores_by_risk()
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