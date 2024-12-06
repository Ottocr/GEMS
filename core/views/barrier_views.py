"""
Barrier Management API Views.

This module contains API endpoints for managing barriers and their assessments.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Q
from django.utils import timezone
from datetime import timedelta
import json

from ..models.barrier_models import (
    Barrier, BarrierCategory, BarrierEffectivenessScore,
    BarrierIssueReport, BarrierScenarioEffectiveness
)
from ..models.asset_models import Asset
from ..models.risk_models import RiskType, RiskSubtype, Scenario, FinalRiskMatrix

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_risk_subtypes(request):
    """API endpoint to get risk subtypes for a specific risk type"""
    risk_type_id = request.GET.get('risk_type')
    if not risk_type_id:
        return JsonResponse([], safe=False)
    
    subtypes = RiskSubtype.objects.filter(risk_type_id=risk_type_id).values('id', 'name')
    return JsonResponse(list(subtypes), safe=False)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_barrier_assessments(request):
    """API endpoint to get list of barrier assessments"""
    barriers = Barrier.objects.select_related(
        'category'
    ).prefetch_related(
        'effectiveness_scores',
        'assets',
        'risk_types',
        'risk_subtypes'
    ).annotate(
        avg_effectiveness=Avg('effectiveness_scores__overall_effectiveness_score')
    )
    
    barriers_data = []
    for barrier in barriers:
        effectiveness_scores = {}
        for score in barrier.effectiveness_scores.all():
            key = f"type_{score.risk_type_id}" if not score.risk_subtype else f"subtype_{score.risk_subtype_id}"
            effectiveness_scores[key] = {
                'risk_type': score.risk_type.name,
                'risk_subtype': score.risk_subtype.name if score.risk_subtype else None,
                'overall': score.overall_effectiveness_score
            }

        barriers_data.append({
            'id': barrier.id,
            'name': barrier.name,
            'description': barrier.description,
            'category': barrier.category.name,
            'avg_effectiveness': barrier.avg_effectiveness,
            'assets_count': barrier.assets.count(),
            'effectiveness_scores': effectiveness_scores,
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
    
    return JsonResponse({
        'success': True,
        'barrier_categories': list(BarrierCategory.objects.values('id', 'name', 'description')),
        'barriers': barriers_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_barrier_details(request, barrier_id):
    """API endpoint to get barrier assessment details"""
    barrier = get_object_or_404(Barrier, id=barrier_id)
    asset_id = request.GET.get('asset')
    asset = get_object_or_404(Asset, id=asset_id) if asset_id else None
    
    # Get effectiveness scores for both risk types and subtypes
    effectiveness_scores = {}
    for score in barrier.effectiveness_scores.all():
        key = f"type_{score.risk_type_id}" if not score.risk_subtype else f"subtype_{score.risk_subtype_id}"
        effectiveness_scores[key] = {
            'risk_type': score.risk_type.name,
            'risk_subtype': score.risk_subtype.name if score.risk_subtype else None,
            'preventive': score.preventive_capability,
            'detection': score.detection_capability,
            'response': score.response_capability,
            'reliability': score.reliability,
            'coverage': score.coverage,
            'overall': score.overall_effectiveness_score
        }
    
    return JsonResponse({
        'success': True,
        'barrier': {
            'id': barrier.id,
            'name': barrier.name,
            'category': barrier.category.name,
            'description': barrier.description,
            'scenarios': list(Scenario.objects.filter(barriers=barrier).values()),
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
            ],
            'effectiveness_scores': effectiveness_scores,
            'asset': {
                'id': asset.id,
                'name': asset.name
            } if asset else None
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_barrier_scenarios(request, barrier_id):
    """API endpoint to save barrier scenario effectiveness"""
    try:
        data = json.loads(request.body)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        with transaction.atomic():
            for scenario_id, effectiveness in data.get('scenarios', {}).items():
                BarrierScenarioEffectiveness.objects.update_or_create(
                    barrier=barrier,
                    scenario_id=scenario_id,
                    defaults={'effectiveness_score': effectiveness}
                )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_barrier_effectiveness(request, barrier_id):
    """API endpoint to save barrier effectiveness scores"""
    try:
        data = json.loads(request.body)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        with transaction.atomic():
            # Handle risk type level scores
            for risk_type_id, scores in data.get('risk_types', {}).items():
                BarrierEffectivenessScore.objects.update_or_create(
                    barrier=barrier,
                    risk_type_id=risk_type_id,
                    risk_subtype=None,
                    defaults={
                        'preventive_capability': scores.get('preventive', 5),
                        'detection_capability': scores.get('detection', 5),
                        'response_capability': scores.get('response', 5),
                        'reliability': scores.get('reliability', 5),
                        'coverage': scores.get('coverage', 5)
                    }
                )
            
            # Handle risk subtype level scores
            for subtype_id, scores in data.get('risk_subtypes', {}).items():
                subtype = get_object_or_404(RiskSubtype, id=subtype_id)
                BarrierEffectivenessScore.objects.update_or_create(
                    barrier=barrier,
                    risk_type=subtype.risk_type,
                    risk_subtype=subtype,
                    defaults={
                        'preventive_capability': scores.get('preventive', 5),
                        'detection_capability': scores.get('detection', 5),
                        'response_capability': scores.get('response', 5),
                        'reliability': scores.get('reliability', 5),
                        'coverage': scores.get('coverage', 5)
                    }
                )
            
            barrier.update_overall_effectiveness()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_barrier_trends(request, barrier_id):
    """API endpoint to get trend data for a specific barrier"""
    barrier = get_object_or_404(Barrier, id=barrier_id)
    
    # Calculate date range
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    # Get historical effectiveness scores
    effectiveness_data = []
    dates = []
    current_date = start_date
    while current_date <= end_date:
        score = barrier.get_overall_effectiveness_score()
        effectiveness_data.append(score)
        dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(days=1)
    
    # Calculate trend
    if len(effectiveness_data) >= 2:
        trend_change = effectiveness_data[-1] - effectiveness_data[0]
        trend_percentage = (trend_change / effectiveness_data[0]) * 100 if effectiveness_data[0] > 0 else 0
        trend_direction = 'up' if trend_change > 0 else 'down' if trend_change < 0 else 'stable'
    else:
        trend_percentage = 0
        trend_direction = 'stable'
    
    # Get risk impacts for both types and subtypes
    risk_impacts = []
    
    # Risk type impacts
    for risk_type in barrier.risk_types.all():
        score = barrier.get_risk_category_effectiveness_score(risk_type)
        risk_impacts.append({
            'name': risk_type.name,
            'type': 'risk_type',
            'reduction': score
        })
    
    # Risk subtype impacts
    for subtype in barrier.risk_subtypes.all():
        score = barrier.get_risk_category_effectiveness_score(subtype.risk_type)
        risk_impacts.append({
            'name': f"{subtype.risk_type.name} - {subtype.name}",
            'type': 'risk_subtype',
            'reduction': score
        })
    
    # Get recent issues
    issues = list(BarrierIssueReport.objects.filter(
        barrier=barrier,
        reported_at__gte=start_date
    ).order_by('-reported_at').values())
    
    return JsonResponse({
        'success': True,
        'trend_data': {
            'dates': dates,
            'effectiveness_scores': effectiveness_data,
            'trend': {
                'direction': trend_direction,
                'percentage': trend_percentage
            },
            'risk_impacts': risk_impacts,
            'issues': issues
        }
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_barrier_issue(request):
    """API endpoint to report an issue with a specific barrier"""
    try:
        data = json.loads(request.body)
        barrier_id = data.get('barrier_id')
        description = data.get('description')
        impact_rating = data.get('impact_rating')
        
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        issue_report = BarrierIssueReport.objects.create(
            barrier=barrier,
            reported_by=request.user,
            description=description,
            impact_rating=impact_rating
        )
        
        # Adjust barrier performance based on the impact rating
        barrier.adjust_performance(impact_rating)
        
        # Trigger the update of barrier effectiveness and risk matrices
        barrier.propagate_effectiveness()
        for asset in barrier.assets.all():
            FinalRiskMatrix.generate_matrices(asset)
        
        return JsonResponse({'success': True, 'message': 'Issue reported successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def resolve_barrier_issue(request, issue_id):
    """API endpoint to resolve a reported barrier issue"""
    try:
        data = json.loads(request.body)
        issue = get_object_or_404(BarrierIssueReport, id=issue_id)
        resolution_notes = data.get('resolution_notes')
        
        issue.status = 'RESOLVED'
        issue.resolved_at = timezone.now()
        issue.resolution_notes = resolution_notes
        issue.save()
        
        # Trigger the update of barrier effectiveness
        issue.barrier.update_overall_effectiveness()
        issue.barrier.propagate_effectiveness()
        
        return JsonResponse({'success': True, 'message': 'Issue resolved successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_barriers_by_category(request, category_id):
    """API endpoint to get barriers for a specific category"""
    category = get_object_or_404(BarrierCategory, id=category_id)
    barriers = Barrier.objects.filter(category=category).prefetch_related(
        'risk_types', 'risk_subtypes'
    ).values('id', 'name')
    
    barriers_data = []
    for barrier in barriers:
        barrier_obj = Barrier.objects.get(id=barrier['id'])
        barriers_data.append({
            'id': barrier['id'],
            'name': barrier['name'],
            'risk_types': [{'id': rt.id, 'name': rt.name} for rt in barrier_obj.risk_types.all()],
            'risk_subtypes': [
                {
                    'id': rs.id,
                    'name': rs.name,
                    'risk_type': {
                        'id': rs.risk_type.id,
                        'name': rs.risk_type.name
                    }
                }
                for rs in barrier_obj.risk_subtypes.all()
            ]
        })
    
    return JsonResponse({
        'success': True,
        'category': {
            'id': category.id,
            'name': category.name,
            'description': category.description
        },
        'barriers': barriers_data
    })
