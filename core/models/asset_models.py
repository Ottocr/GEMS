from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from statistics import mean

# Import models referenced in asset_models.py
from ..models.geo_models import Country
from ..models.risk_models import Scenario, RiskType, RiskScenarioAssessment
from ..models.barrier_models import Barrier, BarrierIssueReport


class AssetType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class AssetLink(models.Model):
    name = models.CharField(max_length=100)
    assets = models.ManyToManyField('Asset', related_name='asset_links')
    shared_risks = models.ManyToManyField('RiskType', related_name='asset_links')
    shared_barriers = models.ManyToManyField('Barrier', related_name='asset_links')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Asset(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    asset_type = models.ForeignKey(AssetType, on_delete=models.CASCADE, related_name='assets')
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='assets')
    criticality_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    vulnerability_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], default=1)
    scenarios = models.ManyToManyField('Scenario', related_name='risk_scenarios', blank=True)
    barriers = models.ManyToManyField('Barrier', related_name='assets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.asset_type.name})"

    def calculate_criticality_score(self):
        asset_criticality_answers = self.asset_criticality_answers.all()
        if not asset_criticality_answers:
            return 1  # Default score if no questions are answered
        
        scores = [answer.selected_score for answer in asset_criticality_answers if answer.selected_score]
        
        if not scores:
            return 1  # Default score if no answers have scores
        
        avg_score = mean(scores)
        return round(avg_score)

    def calculate_vulnerability_score(self):
        asset_vulnerability_answers = self.asset_vulnerability_answers.all()
        if not asset_vulnerability_answers:
            return 1  # Default score if no questions are answered
        
        scores = [answer.selected_score for answer in asset_vulnerability_answers if answer.selected_score]
        
        if not scores:
            return 1  # Default score if no answers have scores
        
        avg_score = mean(scores)
        return round(avg_score)

    def update_scores(self):
        self.criticality_score = self.calculate_criticality_score()
        self.vulnerability_score = self.calculate_vulnerability_score()
        self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def update_risk_assessment_based_on_link(self):
        asset_links = self.asset_links.all()
        for asset_link in asset_links:
            linked_assets = asset_link.assets.exclude(id=self.id)
            shared_risks = asset_link.shared_risks.all()
            shared_barriers = asset_link.shared_barriers.all()

            for linked_asset in linked_assets:
                for risk in shared_risks:
                    self.update_risk_score(linked_asset, risk)
                
                for barrier in shared_barriers:
                    self.update_barrier_effectiveness(linked_asset, barrier)

    def update_risk_score(self, linked_asset, risk):
        # Update risk score logic here
        pass

    def update_barrier_effectiveness(self, linked_asset, barrier):
        # Update barrier effectiveness logic here
        pass

    def create_default_assessments(self):
        scenarios = self.scenarios.all()
        for scenario in scenarios:
            RiskScenarioAssessment.objects.update_or_create(
                asset=self,
                risk_scenario=scenario,
                defaults={
                    'likelihood_rating': 1,
                    'impact_score': 1,
                    'barrier_effectiveness': {},
                    'barrier_performance': {},
                    'residual_risk_score': 1,
                }
            )


    def update_risk_assessment(self):
        # Get all barrier issue reports affecting this asset
        barrier_issues = BarrierIssueReport.objects.filter(affected_assets=self, status__in=['OPEN', 'IN_PROGRESS'])
        
        # Update risk scenario assessments for this asset
        for assessment in self.risk_scenario_assessments.all():
            # Reset barrier performance to default (1.0)
            assessment.barrier_performance = {str(barrier.id): 1.0 for barrier in assessment.risk_scenario.barriers.all()}
            
            # Apply performance adjustments based on barrier issues
            for issue in barrier_issues:
                if issue.barrier in assessment.risk_scenario.barriers.all():
                    performance_adjustment = self.calculate_performance_adjustment(issue.impact_rating)
                    assessment.barrier_performance[str(issue.barrier.id)] *= performance_adjustment
            
            # Recalculate barrier effectiveness and residual risk score
            assessment.calculate_barrier_effectiveness()
            assessment.calculate_residual_risk_score()
            assessment.save()

    @staticmethod
    def calculate_performance_adjustment(impact_rating):
        impact_adjustments = {
            'MINIMAL': 0.9,
            'NO_IMPACT': 1.0,
            'SUBSTANTIAL': 0.7,
            'MAJOR': 0.5,
            'COMPROMISED': 0.1
        }
        return impact_adjustments.get(impact_rating, 1.0)

class AssetVulnerabilityQuestion(models.Model):
    question_text = models.TextField()
    risk_type = models.ForeignKey('RiskType', on_delete=models.CASCADE, related_name='vulnerability_questions')
    choice1 = models.CharField(max_length=255)
    score1 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice2 = models.CharField(max_length=255)
    score2 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice3 = models.CharField(max_length=255)
    score3 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice4 = models.CharField(max_length=255)
    score4 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice5 = models.CharField(max_length=255)
    score5 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.risk_type.name} - {self.question_text[:50]}"

    def get_choices(self):
        return [
            (self.choice1, self.choice1),
            (self.choice2, self.choice2),
            (self.choice3, self.choice3),
            (self.choice4, self.choice4),
            (self.choice5, self.choice5),
        ]

class AssetCriticalityQuestion(models.Model):
    question_text = models.TextField()
    choice1 = models.CharField(max_length=255)
    score1 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice2 = models.CharField(max_length=255)
    score2 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice3 = models.CharField(max_length=255)
    score3 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice4 = models.CharField(max_length=255)
    score4 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    choice5 = models.CharField(max_length=255)
    score5 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question_text[:50]

    def get_choices(self):
        return [
            (self.choice1, self.choice1),
            (self.choice2, self.choice2),
            (self.choice3, self.choice3),
            (self.choice4, self.choice4),
            (self.choice5, self.choice5),
        ]

class AssetVulnerabilityAnswer(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='asset_vulnerability_answers')
    question = models.ForeignKey(AssetVulnerabilityQuestion, on_delete=models.CASCADE, related_name='answers')
    selected_choice = models.CharField(max_length=255, null=True, blank=True)
    selected_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset.name} - {self.question.question_text[:50]}"

    class Meta:
        unique_together = ('asset', 'question')

    def save(self, *args, **kwargs):
        if self.selected_choice:
            if self.selected_choice == self.question.choice1:
                self.selected_score = self.question.score1
            elif self.selected_choice == self.question.choice2:
                self.selected_score = self.question.score2
            elif self.selected_choice == self.question.choice3:
                self.selected_score = self.question.score3
            elif self.selected_choice == self.question.choice4:
                self.selected_score = self.question.score4
            elif self.selected_choice == self.question.choice5:
                self.selected_score = self.question.score5
        super().save(*args, **kwargs)
        self.asset.update_scores()

class AssetCriticalityAnswer(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='asset_criticality_answers')
    question = models.ForeignKey(AssetCriticalityQuestion, on_delete=models.CASCADE, related_name='answers')
    selected_choice = models.CharField(max_length=255, null=True, blank=True)
    selected_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)], null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset.name} - {self.question.question_text[:50]}"

    class Meta:
        unique_together = ('asset', 'question')

    def save(self, *args, **kwargs):
        if self.selected_choice:
            if self.selected_choice == self.question.choice1:
                self.selected_score = self.question.score1
            elif self.selected_choice == self.question.choice2:
                self.selected_score = self.question.score2
            elif self.selected_choice == self.question.choice3:
                self.selected_score = self.question.score3
            elif self.selected_choice == self.question.choice4:
                self.selected_score = self.question.score4
            elif self.selected_choice == self.question.choice5:
                self.selected_score = self.question.score5
        super().save(*args, **kwargs)
        self.asset.update_scores()

@receiver(post_save, sender=Asset)
def create_assessments_on_asset_save(sender, instance, created, **kwargs):
    instance.create_default_assessments()

@receiver(post_save, sender=AssetVulnerabilityQuestion)
def create_blank_vulnerability_answers(sender, instance, created, **kwargs):
    if created:
        assets = Asset.objects.all()
        for asset in assets:
            AssetVulnerabilityAnswer.objects.create(asset=asset, question=instance)

@receiver(post_save, sender=AssetCriticalityQuestion)
def create_blank_criticality_answers(sender, instance, created, **kwargs):
    if created:
        assets = Asset.objects.all()
        for asset in assets:
            AssetCriticalityAnswer.objects.create(asset=asset, question=instance)

@receiver(post_save, sender=BarrierIssueReport)
def update_asset_risk_assessments(sender, instance, **kwargs):
    for asset in instance.affected_assets.all():
        asset.update_risk_assessment()