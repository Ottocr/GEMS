from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from statistics import mean
from django.db import transaction

# Import models referenced in asset_models.py
from ..models.geo_models import Country
from ..models.risk_models import Scenario, RiskType, RiskScenarioAssessment, FinalRiskMatrix
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

    def propagate_changes(self):
        """Propagate changes to all linked assets"""
        with transaction.atomic():
            for asset in self.assets.all():
                asset.update_risk_assessment_based_on_link()

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

    def get_risk_level(self):
        """Calculate overall risk level for the asset"""
        # Get the latest risk matrices for this asset
        risk_matrices = FinalRiskMatrix.objects.filter(asset=self).order_by('-date_generated')
        
        if not risk_matrices.exists():
            # If no risk matrices exist, calculate based on criticality and vulnerability
            return round((self.criticality_score + self.vulnerability_score) / 2, 1)
        
        # Calculate average residual risk score across all risk types
        avg_residual_risk = mean([matrix.residual_risk_score for matrix in risk_matrices])
        
        # Combine with criticality and vulnerability scores
        final_score = (avg_residual_risk + self.criticality_score + self.vulnerability_score) / 3
        return round(final_score, 1)

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
        """Update criticality and vulnerability scores"""
        self.criticality_score = self.calculate_criticality_score()
        self.vulnerability_score = self.calculate_vulnerability_score()
        self.save()
        self.update_risk_assessment()

    @transaction.atomic
    def update_risk_assessment_based_on_link(self):
        """Update risk assessment based on linked assets"""
        asset_links = self.asset_links.all()
        for asset_link in asset_links:
            linked_assets = asset_link.assets.exclude(id=self.id)
            shared_risks = asset_link.shared_risks.all()
            shared_barriers = asset_link.shared_barriers.all()

            for linked_asset in linked_assets:
                # Update risk scores for shared risks
                for risk in shared_risks:
                    self.update_risk_score(linked_asset, risk)
                
                # Update barrier effectiveness for shared barriers
                for barrier in shared_barriers:
                    self.update_barrier_effectiveness(linked_asset, barrier)

        # After updating all scores and effectiveness, recalculate final risk matrix
        FinalRiskMatrix.generate_matrices(self)

    def update_risk_score(self, linked_asset, risk):
        """Update risk scores based on linked asset's risk assessment"""
        # Get risk scenario assessments for both assets
        linked_assessments = RiskScenarioAssessment.objects.filter(
            asset=linked_asset,
            risk_scenario__risk_subtypes__risk_type=risk
        )
        our_assessments = RiskScenarioAssessment.objects.filter(
            asset=self,
            risk_scenario__risk_subtypes__risk_type=risk
        )

        if not linked_assessments or not our_assessments:
            return

        # Calculate average scores from linked asset
        linked_likelihood = mean([a.likelihood_rating for a in linked_assessments])
        linked_impact = mean([a.impact_score for a in linked_assessments])

        # Update our assessments based on linked asset's scores
        # Use weighted average favoring our own assessment (70-30 split)
        for assessment in our_assessments:
            assessment.likelihood_rating = round(
                (assessment.likelihood_rating * 0.7) + (linked_likelihood * 0.3)
            )
            assessment.impact_score = round(
                (assessment.impact_score * 0.7) + (linked_impact * 0.3)
            )
            assessment.calculate_barrier_effectiveness()
            assessment.calculate_residual_risk_score()
            assessment.save()

    def update_barrier_effectiveness(self, linked_asset, barrier):
        """Update barrier effectiveness based on linked asset's barrier performance"""
        # Get barrier effectiveness scores for both assets
        linked_effectiveness = barrier.get_effectiveness_scores_by_risk()
        
        # Get all risk scenario assessments that use this barrier
        assessments = self.risk_scenario_assessments.filter(
            risk_scenario__barriers=barrier
        )

        for assessment in assessments:
            if str(barrier.id) in assessment.barrier_performance:
                # Get current performance
                current_performance = assessment.barrier_performance[str(barrier.id)]
                
                # Get linked asset's performance for this barrier
                linked_performance = linked_asset.risk_scenario_assessments.filter(
                    risk_scenario__barriers=barrier
                ).first()

                if linked_performance and str(barrier.id) in linked_performance.barrier_performance:
                    linked_perf_value = linked_performance.barrier_performance[str(barrier.id)]
                    
                    # Update performance using weighted average (70-30 split)
                    new_performance = (current_performance * 0.7) + (linked_perf_value * 0.3)
                    assessment.barrier_performance[str(barrier.id)] = round(new_performance, 2)
                    
                    # Recalculate effectiveness and risk score
                    assessment.calculate_barrier_effectiveness()
                    assessment.calculate_residual_risk_score()
                    assessment.save()

    def create_default_assessments(self):
        """Create default risk scenario assessments"""
        scenarios = self.scenarios.all()
        for scenario in scenarios:
            RiskScenarioAssessment.objects.update_or_create(
                asset=self,
                risk_scenario=scenario,
                defaults={
                    'likelihood_rating': 1,
                    'impact_score': 1,
                    'barrier_effectiveness': {},
                    'barrier_performance': {str(barrier.id): 1.0 for barrier in scenario.barriers.all()},
                    'residual_risk_score': 1,
                }
            )

    def update_risk_assessment(self):
        """Update risk assessment based on barrier issues"""
        with transaction.atomic():
            # Get all barrier issue reports affecting this asset
            barrier_issues = BarrierIssueReport.objects.filter(
                affected_assets=self,
                status__in=['OPEN', 'IN_PROGRESS']
            )
            
            # Update risk scenario assessments for this asset
            for assessment in self.risk_scenario_assessments.all():
                # Reset barrier performance to default (1.0)
                assessment.barrier_performance = {
                    str(barrier.id): 1.0 for barrier in assessment.risk_scenario.barriers.all()
                }
                
                # Apply performance adjustments based on barrier issues
                for issue in barrier_issues:
                    if issue.barrier in assessment.risk_scenario.barriers.all():
                        performance_adjustment = self.calculate_performance_adjustment(issue.impact_rating)
                        assessment.barrier_performance[str(issue.barrier.id)] *= performance_adjustment
                
                # Recalculate barrier effectiveness and residual risk score
                assessment.calculate_barrier_effectiveness()
                assessment.calculate_residual_risk_score()
                assessment.save()

            # Update final risk matrix
            FinalRiskMatrix.generate_matrices(self)

    @staticmethod
    def calculate_performance_adjustment(impact_rating):
        """Calculate performance adjustment based on impact rating"""
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