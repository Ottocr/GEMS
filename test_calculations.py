"""
Test script to verify GEMS risk assessment calculations.
This script tests the accuracy of:
1. Barrier effectiveness calculations
2. Risk score calculations
3. Overall risk matrix calculations
4. BTA and geographical impact calculations
"""

import os
import sys
import django
from decimal import Decimal
from statistics import mean

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gems.settings')
django.setup()

from core.models.barrier_models import (
    Barrier, BarrierEffectivenessScore, BarrierCategory
)
from core.models.asset_models import Asset
from core.models.risk_models import (
    RiskType, RiskSubtype, Scenario, RiskScenarioAssessment,
    BaselineThreatAssessment, FinalRiskMatrix
)
from core.models.geo_models import Country, Continent

def test_barrier_effectiveness():
    """Test barrier effectiveness calculations"""
    print("\n=== Testing Barrier Effectiveness Calculations ===")
    
    barriers = Barrier.objects.all()
    for barrier in barriers:
        print(f"\nTesting barrier: {barrier.name}")
        
        # Test individual effectiveness scores
        for score in barrier.effectiveness_scores.all():
            print(f"\nTesting effectiveness score for {score}")
            
            # Calculate weighted score
            expected_score = round(
                score.preventive_capability * 0.30 +
                score.detection_capability * 0.20 +
                score.response_capability * 0.20 +
                score.reliability * 0.15 +
                score.coverage * 0.15,
                2
            )
            
            assert score.overall_effectiveness_score == expected_score, \
                f"Expected {expected_score}, got {score.overall_effectiveness_score}"
            
            print(f"Individual score components:")
            print(f"Preventive (30%): {score.preventive_capability * 0.30}")
            print(f"Detection (20%): {score.detection_capability * 0.20}")
            print(f"Response (20%): {score.response_capability * 0.20}")
            print(f"Reliability (15%): {score.reliability * 0.15}")
            print(f"Coverage (15%): {score.coverage * 0.15}")
            print(f"Total: {expected_score}")
        
        # Test overall effectiveness
        overall_score = barrier.get_overall_effectiveness_score()
        print(f"\nOverall effectiveness score: {overall_score}")
        
        # Verify the calculation
        scores = barrier.effectiveness_scores.all()
        expected_base = mean([score.overall_effectiveness_score for score in scores])
        expected_score = round(expected_base * barrier.performance_adjustment, 2)
        
        assert overall_score == expected_score, \
            f"Expected {expected_score}, got {overall_score}"

def test_risk_scenario_calculations():
    """Test risk scenario assessment calculations"""
    print("\n=== Testing Risk Scenario Calculations ===")
    
    assets = Asset.objects.all()
    for asset in assets:
        print(f"\nTesting asset: {asset.name}")
        
        assessments = RiskScenarioAssessment.objects.filter(asset=asset)
        for assessment in assessments:
            print(f"\nScenario: {assessment.scenario.name}")
            
            # Calculate base risk using geometric mean
            base_risk = (assessment.likelihood_score * 
                        assessment.impact_score * 
                        assessment.vulnerability_score) ** (1/3)
            
            # Calculate barrier effectiveness
            barrier_effectiveness = assessment._calculate_barrier_effectiveness()
            avg_effectiveness = 0
            if barrier_effectiveness:
                # Use raw effectiveness values (already scaled 0-10)
                effectiveness_values = [float(v) for v in barrier_effectiveness.values()]
                if effectiveness_values:
                    avg_effectiveness = mean(effectiveness_values)
            
            # Calculate expected residual risk using the model's formula
            expected_risk = round(base_risk / (1 + avg_effectiveness), 5)
            
            print(f"Input values:")
            print(f"Likelihood: {assessment.likelihood_score}")
            print(f"Impact: {assessment.impact_score}")
            print(f"Vulnerability: {assessment.vulnerability_score}")
            print(f"\nCalculations:")
            print(f"Base Risk (L*I*V)^1/3: {base_risk}")
            print(f"Barrier Effectiveness Values: {barrier_effectiveness}")
            print(f"Average Effectiveness: {avg_effectiveness}")
            print(f"Expected Residual Risk: {expected_risk}")
            print(f"Actual Residual Risk: {assessment.residual_risk_score}")
            
            # Allow for small floating point differences
            assert abs(assessment.residual_risk_score - expected_risk) < 0.01, \
                f"Expected {expected_risk}, got {assessment.residual_risk_score}"

def test_bta_calculations():
    """Test BTA calculations and geographical impact"""
    print("\n=== Testing BTA and Geographical Impact ===")
    
    countries = Country.objects.filter(company_operated=True)
    for country in countries:
        print(f"\nTesting country: {country.name}")
        
        # Verify BTAs exist for all risk types
        risk_types = RiskType.objects.all()
        for risk_type in risk_types:
            bta = BaselineThreatAssessment.objects.filter(
                risk_type=risk_type,
                country=country
            ).order_by('-date_assessed').first()
            
            assert bta is not None, \
                f"Missing BTA for risk type {risk_type.name} in {country.name}"
            
            print(f"\nRisk Type: {risk_type.name}")
            print(f"BTA Score: {bta.baseline_score}")
            print(f"Impact on Assets: {bta.impact_on_assets}")
            
            # Test BTA impact on assets in this country
            assets = Asset.objects.filter(country=country)
            for asset in assets:
                matrices = FinalRiskMatrix.objects.filter(
                    asset=asset,
                    risk_type=risk_type
                )
                
                for matrix in matrices:
                    # Get scenario-based risk score
                    assessments = RiskScenarioAssessment.objects.filter(
                        asset=asset,
                        scenario__risk_subtypes__risk_type=risk_type
                    )
                    
                    if assessments:
                        avg_residual_risk = mean([a.residual_risk_score for a in assessments])
                        
                        # Calculate expected final score with BTA
                        if bta.impact_on_assets:
                            expected_score = round((avg_residual_risk + bta.baseline_score) / 2, 2)
                        else:
                            expected_score = round(avg_residual_risk, 2)
                        
                        print(f"\nAsset: {asset.name}")
                        print(f"Average Residual Risk: {avg_residual_risk}")
                        print(f"Expected Score with BTA: {expected_score}")
                        print(f"Actual Matrix Score: {matrix.residual_risk_score}")
                        
                        # Allow for small floating point differences
                        assert abs(matrix.residual_risk_score - expected_score) < 0.01, \
                            f"Expected {expected_score}, got {matrix.residual_risk_score}"

def test_risk_matrix_calculations():
    """Test final risk matrix calculations"""
    print("\n=== Testing Risk Matrix Calculations ===")
    
    assets = Asset.objects.all()
    for asset in assets:
        print(f"\nTesting asset: {asset.name}")
        print(f"Country: {asset.country.name}")
        
        matrices = FinalRiskMatrix.objects.filter(asset=asset)
        for matrix in matrices:
            print(f"\nRisk Type: {matrix.risk_type.name}")
            
            # Get all scenario assessments for this risk type
            assessments = RiskScenarioAssessment.objects.filter(
                asset=asset,
                scenario__risk_subtypes__risk_type=matrix.risk_type
            )
            
            if assessments:
                # Calculate average residual risk
                residual_risks = [a.residual_risk_score for a in assessments]
                avg_residual_risk = mean(residual_risks)
                
                # Get BTA score if available
                bta = BaselineThreatAssessment.objects.filter(
                    risk_type=matrix.risk_type,
                    country=asset.country
                ).order_by('-date_assessed').first()
                
                # Calculate expected final score
                if bta and bta.impact_on_assets:
                    expected_score = round((avg_residual_risk + bta.baseline_score) / 2, 2)
                    print(f"BTA Score: {bta.baseline_score}")
                else:
                    expected_score = round(avg_residual_risk, 2)
                
                print(f"Calculations:")
                print(f"Scenario Assessments: {len(assessments)}")
                print(f"Residual Risks: {residual_risks}")
                print(f"Average Residual Risk: {avg_residual_risk}")
                print(f"Expected Final Score: {expected_score}")
                print(f"Actual Score: {matrix.residual_risk_score}")
                
                # Allow for small floating point differences
                assert abs(matrix.residual_risk_score - expected_score) < 0.01, \
                    f"Expected {expected_score}, got {matrix.residual_risk_score}"
                
                # Verify risk level calculation
                expected_level = FinalRiskMatrix.calculate_risk_level(expected_score)
                assert matrix.risk_level == expected_level, \
                    f"Expected level {expected_level}, got {matrix.risk_level}"

def main():
    """Run all calculation tests"""
    try:
        test_barrier_effectiveness()
        print("\n✓ Barrier effectiveness calculations verified")
        
        test_risk_scenario_calculations()
        print("\n✓ Risk scenario calculations verified")
        
        test_bta_calculations()
        print("\n✓ BTA and geographical impact calculations verified")
        
        test_risk_matrix_calculations()
        print("\n✓ Risk matrix calculations verified")
        
        print("\n=== All Calculations Verified Successfully ===")
        
    except AssertionError as e:
        print(f"\n❌ Calculation verification failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
