from django.db.models.signals import post_save
from django.dispatch import receiver
from .model_imports import (
    get_risk_type_model,
    get_country_model,
    get_baseline_threat_assessment_model,
    get_final_risk_matrix_model,
    get_risk_log_model,
    get_risk_scenario_assessment_model,
    get_barrier_issue_report_model,
    get_asset_model
)

@receiver(post_save, sender=get_risk_type_model())
def create_bta_for_risk_type(sender, instance, created, **kwargs):
    if created:
        Country = get_country_model()
        BaselineThreatAssessment = get_baseline_threat_assessment_model()
        countries = Country.objects.filter(company_operated=True)
        for country in countries:
            BaselineThreatAssessment.objects.get_or_create(
                risk_type=instance,
                country=country,
                defaults={
                    'baseline_score': 5,
                    'impact_on_assets': True,
                    'notes': 'Automatically created for new risk type.',
                }
            )

@receiver(post_save, sender=get_final_risk_matrix_model())
def create_risk_log(sender, instance, created, **kwargs):
    if created:
        RiskLog = get_risk_log_model()
        BaselineThreatAssessment = get_baseline_threat_assessment_model()
        RiskLog.objects.create(
            asset=instance.asset,
            risk_type=instance.risk_type,
            bta_score=BaselineThreatAssessment.objects.filter(risk_type=instance.risk_type, country=instance.asset.country).latest('date_assessed').baseline_score,
            vulnerability_score=instance.asset.vulnerability_score,
            criticality_score=instance.asset.criticality_score,
            residual_risk_score=instance.residual_risk_score
        )

@receiver(post_save, sender=get_asset_model())
def update_risk_matrices_for_asset(sender, instance, created, **kwargs):
    FinalRiskMatrix = get_final_risk_matrix_model()
    FinalRiskMatrix.generate_matrices(instance)

@receiver(post_save, sender=get_risk_scenario_assessment_model())
def update_risk_matrices_for_scenario(sender, instance, created, **kwargs):
    FinalRiskMatrix = get_final_risk_matrix_model()
    FinalRiskMatrix.generate_matrices(instance.asset)

@receiver(post_save, sender=get_barrier_issue_report_model())
def update_barrier_effectiveness(sender, instance, **kwargs):
    instance.barrier.adjust_performance(instance.impact_rating)
    
    if instance.status == 'RESOLVED':
        instance.barrier.update_overall_effectiveness()
        instance.barrier.propagate_effectiveness()
        
        # Update linked assets
        for asset_link in instance.barrier.asset_links.all():
            for asset in asset_link.assets.all():
                asset.update_risk_assessment_based_on_link()