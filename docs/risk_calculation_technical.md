# GEMS Risk Calculation Technical Implementation

## System Architecture

### Core Models
The risk calculation system is built around four primary model groups:

1. **Barrier Models**
```python
class Barrier:
    - name, description, category
    - performance_adjustment (float)
    - risk_types, risk_subtypes (M2M)
    - effectiveness_scores (reverse relation)
    
class BarrierEffectivenessScore:
    - barrier (FK)
    - risk_type, risk_subtype (FK)
    - preventive_capability (1-10)
    - detection_capability (1-10)
    - response_capability (1-10)
    - reliability (1-10)
    - coverage (1-10)
```

2. **Risk Models**
```python
class RiskScenarioAssessment:
    - asset, scenario (FK)
    - likelihood_score (float)
    - impact_score (float)
    - vulnerability_score (float)
    - barrier_effectiveness (JSON)
    - residual_risk_score (float)

class FinalRiskMatrix:
    - asset, risk_type (FK)
    - residual_risk_score (float)
    - risk_level (enum)
    - sub_risk_details (JSON)
    - barrier_details (JSON)
```

3. **Geographic Models**
```python
class BaselineThreatAssessment:
    - risk_type, country (FK)
    - baseline_score (1-10)
    - impact_on_assets (boolean)
```

4. **Asset Models**
```python
class Asset:
    - name, description
    - country (FK)
    - criticality_score (1-10)
    - vulnerability_score (1-10)
    - scenarios, barriers (M2M)
```

### Key Database Considerations
- Extensive use of foreign keys for data integrity
- JSON fields for flexible data storage
- Optimized indexes on frequently queried fields
- Atomic transactions for critical updates

## Implementation Details

### 1. Barrier Effectiveness Calculation

```python
def calculate_overall_effectiveness(self):
    """Calculate weighted effectiveness score."""
    return round(
        self.preventive_capability * 0.30 +
        self.detection_capability * 0.20 +
        self.response_capability * 0.20 +
        self.reliability * 0.15 +
        self.coverage * 0.15,
        2
    )
```

### 2. Risk Scenario Assessment

```python
def calculate_scores(self):
    """Calculate risk scores for a scenario."""
    # Calculate base risk
    base_risk = (
        self.likelihood_score * 
        self.impact_score * 
        self.vulnerability_score
    ) ** (1/3)
    
    # Calculate barrier effectiveness
    effectiveness = self._calculate_barrier_effectiveness()
    
    if effectiveness:
        avg_effectiveness = mean(effectiveness.values())
        self.residual_risk_score = base_risk / (1 + avg_effectiveness)
    else:
        self.residual_risk_score = base_risk
```

### 3. Risk Matrix Generation

```python
@classmethod
def generate_matrices(cls, asset):
    """Generate risk matrices for an asset."""
    risk_types = RiskType.objects.filter(
        subtypes__scenarios__assessments__asset=asset
    ).distinct()
    
    for risk_type in risk_types:
        assessments = RiskScenarioAssessment.objects.filter(
            asset=asset,
            scenario__risk_subtypes__risk_type=risk_type
        )
        
        if assessments.exists():
            avg_residual_risk = mean([
                a.residual_risk_score for a in assessments
            ])
            
            bta = BaselineThreatAssessment.objects.filter(
                risk_type=risk_type,
                country=asset.country
            ).latest('date_assessed')
            
            final_score = (
                avg_residual_risk + bta.baseline_score
            ) / 2 if bta else avg_residual_risk
            
            cls.objects.update_or_create(
                asset=asset,
                risk_type=risk_type,
                defaults={
                    'residual_risk_score': final_score,
                    'risk_level': cls.calculate_risk_level(final_score)
                }
            )
```

## Performance Optimization

### 1. Database Query Optimization
- Use of `select_related()` and `prefetch_related()` for related objects
- Bulk create/update operations where possible
- Strategic use of database indexes

```python
# Example of optimized querying
barriers = Barrier.objects.select_related('category').prefetch_related(
    'effectiveness_scores',
    'risk_types',
    'risk_subtypes'
).filter(is_active=True)
```

### 2. Caching Strategy
- Cache barrier effectiveness scores
- Cache BTA values for active countries
- Invalidate caches on relevant updates

### 3. Asynchronous Processing
- Background task processing for non-critical updates
- Queued recalculations for bulk changes

## Data Validation and Integrity

### 1. Model-Level Validation
```python
class BarrierEffectivenessScore(models.Model):
    preventive_capability = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    # Similar validators for other scores
```

### 2. Transaction Management
```python
@transaction.atomic
def update_risk_assessment(self):
    """Update risk assessment with transaction safety."""
    self.calculate_scores()
    self.save()
    FinalRiskMatrix.generate_matrices(self.asset)
```

### 3. Signal Handlers
```python
@receiver(post_save, sender=BarrierIssueReport)
def update_asset_risk_assessments(sender, instance, **kwargs):
    """Trigger risk recalculation on barrier issues."""
    for asset in instance.affected_assets.all():
        asset.update_risk_assessment()
```

## Testing and Quality Assurance

### 1. Unit Tests
- Test individual calculation components
- Validate edge cases and boundary conditions
- Verify mathematical accuracy

### 2. Integration Tests
- Test complete calculation chain
- Verify data consistency across models
- Test transaction integrity

### 3. Automated Calculation Verification
- Regular automated testing of all calculations
- Comparison with known good results
- Performance benchmarking

## System Monitoring

### 1. Calculation Logging
```python
logger.debug(f"Base Risk: {base_risk}")
logger.debug(f"Barrier Effectiveness: {effectiveness}")
logger.debug(f"Final Score: {final_score}")
```

### 2. Performance Metrics
- Track calculation times
- Monitor database query performance
- Log memory usage patterns

### 3. Error Handling
```python
try:
    assessment.calculate_scores()
except Exception as e:
    logger.error(f"Error calculating scores: {str(e)}")
    raise CalculationError(f"Failed to calculate risk scores: {str(e)}")
```

## Maintenance and Updates

### 1. Database Migrations
- Careful handling of schema changes
- Data migration strategies
- Backward compatibility considerations

### 2. Code Updates
- Version control best practices
- Documentation requirements
- Testing requirements

### 3. Deployment Considerations
- Zero-downtime updates where possible
- Database backup requirements
- Rollback procedures
