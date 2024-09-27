from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from ..models.asset_models import Asset
from ..models.risk_models import RiskType


class RiskLog(models.Model):
    asset = models.ForeignKey('core.Asset', on_delete=models.CASCADE, related_name='risk_logs')
    risk_type = models.ForeignKey('core.RiskType', on_delete=models.CASCADE, related_name='risk_logs')
    bta_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    vulnerability_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    criticality_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    residual_risk_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Risk Log for {self.asset.name} - {self.risk_type.name} at {self.timestamp}"