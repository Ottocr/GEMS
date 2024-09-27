from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

class Continent(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Country(models.Model):
    name = models.CharField(max_length=100, unique=True)  
    code = models.CharField(max_length=3, null=True, blank=True)  
    geo_data = models.JSONField(null=True, blank=True)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name='countries')
    company_operated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name_plural = "Countries"

@receiver(post_save, sender=Country)
def create_bta_for_country(sender, instance, created, **kwargs):
    if instance.company_operated:
        from .risk_models import RiskType, BaselineThreatAssessment
        risk_types = RiskType.objects.all()
        for risk_type in risk_types:
            BaselineThreatAssessment.objects.get_or_create(
                risk_type=risk_type,
                country=instance,
                defaults={
                    'baseline_score': 5,
                    'impact_on_assets': True,
                    'notes': 'Automatically created for new company-operated country.',
                }
            )
