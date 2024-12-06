"""
Risk Assessment API Views.
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
import json

from ..models.asset_models import (
    Asset, AssetVulnerabilityAnswer, AssetCriticalityAnswer
)
from ..models.barrier_models import (
    Barrier, BarrierEffectivenessScore
)
from ..models.risk_models import (
    BaselineThreatAssessment, RiskType, RiskSubtype,
    Scenario, RiskScenarioAssessment, FinalRiskMatrix
)
from ..models.log_models import RiskLog

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_risk_assessment_data(request):
    """API endpoint for risk assessment workflow data."""
    assets = Asset.objects.select_related(
        'asset_type', 'country'
    ).prefetch_related(
        'barriers', 'scenarios',
        'risk_scenario_assessments'
    )
    
    barriers = Barrier.objects.select_related(
        'category'
    ).prefetch_related(
        'effectiveness_scores',
        'risk_types',
        'risk_subtypes'
    ).annotate(
        avg_effectiveness=Avg('effectiveness_scores__overall_effectiveness_score')
    )
    
    risk_types = RiskType.objects.prefetch_related('subtypes')
    scenarios = Scenario.objects.prefetch_related('risk_subtypes', 'barriers')
    
    # Convert assets to JSON format
    assets_data = []
    for asset in assets:
        assets_data.append({
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
    
    # Convert barriers to JSON format with risk associations
    barriers_data = []
    for barrier in barriers:
        barriers_data.append({
            'id': barrier.id,
            'name': barrier.name,
            'category': barrier.category.name,
            'description': barrier.description,
            'avg_effectiveness': barrier.avg_effectiveness,
            'risk_types': [{'id': rt.id, 'name': rt.name} for rt in barrier.risk_types.all()],
            'risk_subtypes': [
                {
                    'id': rs.id,
                    'name': rs.name,
                    'risk_type': {
                        'id': rs.risk_type.id,
                        'name': rs.risk_type.name
                    }
                }
                for rs in barrier.risk_subtypes.all()
            ]
        })

    # Convert risk types to JSON format with subtypes
    risk_types_data = []
    for risk_type in risk_types:
        risk_types_data.append({
            'id': risk_type.id,
            'name': risk_type.name,
            'description': risk_type.description,
            'subtypes': [
                {
                    'id': subtype.id,
                    'name': subtype.name,
                    'description': subtype.description
                }
                for subtype in risk_type.subtypes.all()
            ]
        })

    # Convert scenarios to JSON format with risk associations
    scenarios_data = []
    for scenario in scenarios:
        scenarios_data.append({
            'id': scenario.id,
            'name': scenario.name,
            'description': scenario.description,
            'risk_subtypes': [
                {
                    'id': rs.id,
                    'name': rs.name,
                    'risk_type': {
                        'id': rs.risk_type.id,
                        'name': rs.risk_type.name
                    }
                }
                for rs in scenario.risk_subtypes.all()
            ],
            'barriers': [
                {
                    'id': barrier.id,
                    'name': barrier.name,
                    'category': barrier.category.name
                }
                for barrier in scenario.barriers.all()
            ]
        })

    return Response({
        'assets': assets_data,
        'barriers': barriers_data,
        'risk_types': risk_types_data,
        'scenarios': scenarios_data
    })

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_risk_assessment(request):
    """API endpoint to save the complete risk assessment."""
    try:
        data = request.data
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
            
        return Response({'success': True})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=400)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_risk_matrix_data(request):
    """API endpoint to get risk matrix data."""
    assets = Asset.objects.all()
    risk_types = RiskType.objects.all()
    
    return Response({
        'assets': list(assets.values('id', 'name', 'asset_type__name')),
        'risk_types': list(risk_types.values()),
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def generate_risk_matrix(request):
    """API endpoint to generate risk matrix visualization data."""
    asset_id = request.GET.get('asset_id')
    risk_type_id = request.GET.get('risk_type_id')
    
    if not asset_id or not risk_type_id:
        return Response({'success': False, 'error': 'Missing parameters'}, status=400)
    
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
    
    return Response({
        'success': True,
        'matrix': matrix
    })

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_step_data(request):
    """API endpoint to save risk matrix step data."""
    try:
        data = request.data
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
        
        return Response({'success': True})
    except Exception as e:
        return Response({'success': False, 'error': str(e)}, status=400)

