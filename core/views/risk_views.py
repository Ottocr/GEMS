"""
Risk Assessment Views.

This module contains views related to risk assessment workflows and risk matrix generation.
It handles the complete risk assessment process, from initial assessment to final risk
matrix generation.

Main components:
- Risk assessment workflow
- Risk matrix generation
- Step-by-step assessment process
- Risk scenario evaluation
- Barrier effectiveness integration

The risk views implement the core risk assessment methodology, combining:
- Baseline Threat Assessments (BTAs)
- Asset vulnerability and criticality
- Barrier effectiveness
- Scenario likelihood and impact

This creates a comprehensive risk assessment that helps identify and prioritize risks
across assets and locations.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count, Q
import json

from ..models.asset_models import (
    Asset, AssetVulnerabilityAnswer, AssetCriticalityAnswer
)
from ..models.barrier_models import (
    Barrier, BarrierCharacteristicAssessment,
    BarrierEffectivenessScore
)
from ..models.risk_models import (
    BaselineThreatAssessment, RiskType, RiskSubtype,
    Scenario, RiskScenarioAssessment, FinalRiskMatrix
)
from ..models.log_models import RiskLog

@login_required
def risk_assessment_workflow(request):
    """Main view for the step-by-step risk assessment workflow.
    
    The workflow consists of several steps:
    1. Asset Selection and Context
    2. Baseline Threat Assessment Review
    3. Vulnerability Assessment
    4. Criticality Assessment
    5. Scenario Evaluation
    6. Barrier Assessment
    7. Final Risk Matrix Generation
    
    Each step builds upon the previous ones to create a comprehensive
    risk assessment for the selected asset.
    """
    assets = Asset.objects.select_related(
        'asset_type', 'country'
    ).prefetch_related(
        'barriers', 'scenarios',
        'risk_scenario_assessments'
    ).annotate(
        high_risks=Count('risk_scenario_assessments',
            filter=Q(risk_scenario_assessments__residual_risk_score__gt=7)
        ),
        medium_risks=Count('risk_scenario_assessments',
            filter=Q(
                risk_scenario_assessments__residual_risk_score__gt=4,
                risk_scenario_assessments__residual_risk_score__lte=7
            )
        ),
        low_risks=Count('risk_scenario_assessments',
            filter=Q(risk_scenario_assessments__residual_risk_score__lte=4)
        )
    )
    
    barriers = Barrier.objects.select_related(
        'category'
    ).prefetch_related(
        'effectiveness_scores',
        'characteristic_assessments'
    ).annotate(
        avg_effectiveness=Avg('effectiveness_scores__overall_effectiveness_score')
    )
    
    risk_types = RiskType.objects.prefetch_related('subtypes')
    scenarios = Scenario.objects.prefetch_related('risk_subtypes', 'barriers')
    
    # Convert assets to JSON for map
    assets_json = []
    for asset in assets:
        assets_json.append({
            'id': asset.id,
            'name': asset.name,
            'asset_type': asset.asset_type.name,
            'latitude': asset.latitude,
            'longitude': asset.longitude,
            'criticality_score': asset.criticality_score,
            'vulnerability_score': asset.vulnerability_score,
            'country': {
                'name': asset.country.name,
                'code': asset.country.code
            }
        })
    
    context = {
        'assets': assets,
        'assets_json': json.dumps(assets_json),
        'barriers': barriers,
        'risk_types': risk_types,
        'scenarios': scenarios
    }
    
    return render(request, 'risk_assessment_workflow.html', context)

@login_required
@csrf_exempt
def save_risk_assessment(request):
    """Save the complete risk assessment from the workflow.
    
    Handles saving of:
    - BTA scores
    - Scenario assessments
    - Barrier configurations
    - Effectiveness scores
    
    Also triggers:
    - Final risk matrix generation
    - Risk log creation
    - Asset risk score updates
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        asset_id = data.get('selectedAsset')
        risk_assessments = data.get('riskAssessments', {})
        barrier_configs = data.get('barrierConfigurations', {})
        
        with transaction.atomic():
            asset = get_object_or_404(Asset, id=asset_id)
            
            # Save BTA scores
            for risk_type_id, score in risk_assessments.get('bta', {}).items():
                BaselineThreatAssessment.objects.update_or_create(
                    risk_type_id=risk_type_id,
                    country=asset.country,
                    defaults={'baseline_score': score}
                )
            
            # Save scenario assessments
            for scenario_id, assessment in risk_assessments.get('scenarios', {}).items():
                RiskScenarioAssessment.objects.update_or_create(
                    asset=asset,
                    risk_scenario_id=scenario_id,
                    defaults={
                        'likelihood_rating': assessment.get('likelihood', 1),
                        'impact_score': assessment.get('impact', 1)
                    }
                )
            
            # Save barrier configurations
            for barrier_id, config in barrier_configs.items():
                barrier = Barrier.objects.get(id=barrier_id)
                
                # Save characteristic assessments
                for char_id, value in config.get('characteristics', {}).items():
                    BarrierCharacteristicAssessment.objects.update_or_create(
                        barrier=barrier,
                        characteristic_id=char_id,
                        defaults={
                            'selected_value': value,
                            'score': next(
                                (item['score'] for item in barrier.category.characteristics.get(id=char_id).possible_values 
                                if item['value'] == value),
                                5  # Default score if no match found
                            )
                        }
                    )
                
                # Save effectiveness scores
                for risk_type_id, scores in config.get('effectiveness', {}).items():
                    BarrierEffectivenessScore.objects.update_or_create(
                        barrier=barrier,
                        risk_type_id=risk_type_id,
                        defaults={
                            'preventive_capability': scores.get('preventive', 5),
                            'detection_capability': scores.get('detection', 5),
                            'response_capability': scores.get('response', 5),
                            'reliability': scores.get('reliability', 5),
                            'coverage': scores.get('coverage', 5)
                        }
                    )
            
            # Update final risk matrices
            FinalRiskMatrix.generate_matrices(asset)
            
            # Create log entry
            RiskLog.objects.create(
                asset=asset,
                risk_type_id=data.get('primaryRiskType'),
                bta_score=asset.country.baseline_threats.filter(
                    risk_type_id=data.get('primaryRiskType')
                ).first().baseline_score,
                vulnerability_score=asset.vulnerability_score,
                criticality_score=asset.criticality_score,
                residual_risk_score=FinalRiskMatrix.objects.filter(
                    asset=asset,
                    risk_type_id=data.get('primaryRiskType')
                ).first().residual_risk_score
            )
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def risk_matrix_generator(request):
    """Generate risk matrices for assets.
    
    Creates visual risk matrices showing:
    - Likelihood vs Impact plots
    - Scenario distribution
    - Risk levels by color
    - Barrier effectiveness indicators
    """
    assets = Asset.objects.all()
    risk_types = RiskType.objects.all()
    
    context = {
        'assets': assets,
        'risk_types': risk_types,
    }
    
    return render(request, 'risk_matrix_generator.html', context)

@login_required
def generate_risk_matrix(request):
    """Generate risk matrix data for visualization.
    
    Creates a 5x5 matrix showing:
    - Scenario placement based on likelihood and impact
    - Color coding for risk levels
    - Barrier effectiveness indicators
    - Risk reduction arrows
    """
    asset_id = request.GET.get('asset_id')
    risk_type_id = request.GET.get('risk_type_id')
    
    if not asset_id or not risk_type_id:
        return JsonResponse({'success': False, 'error': 'Missing parameters'})
    
    asset = get_object_or_404(Asset, id=asset_id)
    risk_type = get_object_or_404(RiskType, id=risk_type_id)
    
    # Get scenarios for this risk type
    scenarios = RiskScenarioAssessment.objects.filter(
        asset=asset,
        risk_scenario__risk_subtypes__risk_type=risk_type
    ).select_related('risk_scenario')
    
    # Initialize matrix
    matrix = {}
    for likelihood in range(1, 6):
        for impact in range(1, 6):
            key = f"{likelihood}_{impact}"
            matrix[key] = []
    
    # Populate matrix with scenarios
    for assessment in scenarios:
        key = f"{assessment.likelihood_rating}_{assessment.impact_score}"
        matrix[key].append({
            'id': assessment.risk_scenario.id,
            'name': assessment.risk_scenario.name,
            'description': assessment.risk_scenario.description
        })
    
    return JsonResponse({
        'success': True,
        'matrix': matrix
    })

@login_required
@csrf_exempt
def save_step_data(request):
    """Save risk matrix step data during the assessment workflow.
    
    Handles saving of:
    - Vulnerability assessment answers
    - Criticality assessment answers
    - Barrier configurations
    - Risk matrices
    
    Updates scores and triggers matrix generation after each step.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')
        step = data.get('step')
        step_data = data.get('data', {})
        
        asset = get_object_or_404(Asset, id=asset_id)
        
        with transaction.atomic():
            if step == 'vulnerability':
                for question_id, answer in step_data.items():
                    AssetVulnerabilityAnswer.objects.update_or_create(
                        asset=asset,
                        question_id=question_id,
                        defaults={'answer': answer}
                    )
                asset.update_vulnerability_score()
            
            elif step == 'criticality':
                for question_id, answer in step_data.items():
                    AssetCriticalityAnswer.objects.update_or_create(
                        asset=asset,
                        question_id=question_id,
                        defaults={'answer': answer}
                    )
                asset.update_criticality_score()
            
            elif step == 'barriers':
                asset.barriers.set(step_data.get('selected_barriers', []))
                
                for barrier_id, config in step_data.get('configurations', {}).items():
                    barrier = Barrier.objects.get(id=barrier_id)
                    for risk_type_id, scores in config.items():
                        BarrierEffectivenessScore.objects.update_or_create(
                            barrier=barrier,
                            risk_type_id=risk_type_id,
                            defaults=scores
                        )
            
            # Generate final risk matrices
            FinalRiskMatrix.generate_matrices(asset)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
