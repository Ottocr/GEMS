"""
Analysis API Views.

This module contains API endpoints for analyzing risk data and generating recommendations.
It provides trend analysis, risk insights, and actionable recommendations based on
risk assessments, barrier effectiveness, and historical data.
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

from ..models.asset_models import Asset
from ..models.barrier_models import Barrier
from ..models.risk_models import RiskType, RiskScenarioAssessment
from ..models.log_models import RiskLog

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_trend_analysis(request):
    """API endpoint to get trend analysis data for risk assessments."""
    asset_id = request.GET.get('asset_id')
    risk_type_id = request.GET.get('risk_type_id')
    timeframe = request.GET.get('timeframe', '30')  # Default to 30 days
    
    asset = get_object_or_404(Asset, id=asset_id)
    risk_type = get_object_or_404(RiskType, id=risk_type_id)
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=int(timeframe))
    
    risk_logs = RiskLog.objects.filter(
        asset=asset,
        risk_type=risk_type,
        timestamp__range=(start_date, end_date)
    ).order_by('timestamp')
    
    trend_data = {
        'asset_info': {
            'id': asset.id,
            'name': asset.name,
            'type': asset.asset_type.name
        },
        'risk_type_info': {
            'id': risk_type.id,
            'name': risk_type.name
        },
        'timeframe': timeframe,
        'data_points': [{
            'date': log.timestamp.strftime('%Y-%m-%d'),
            'bta_score': log.bta_score,
            'vulnerability_score': log.vulnerability_score,
            'criticality_score': log.criticality_score,
            'residual_risk_score': log.residual_risk_score,
        } for log in risk_logs],
        'summary': {
            'average_bta': risk_logs.aggregate(Avg('bta_score'))['bta_score__avg'],
            'average_vulnerability': risk_logs.aggregate(Avg('vulnerability_score'))['vulnerability_score__avg'],
            'average_criticality': risk_logs.aggregate(Avg('criticality_score'))['criticality_score__avg'],
            'average_residual_risk': risk_logs.aggregate(Avg('residual_risk_score'))['residual_risk_score__avg'],
        }
    }
    
    return Response({
        'success': True,
        'trend_analysis': trend_data
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_recommendations(request, asset_id):
    """API endpoint to get recommendations based on risk assessment."""
    asset = get_object_or_404(Asset, id=asset_id)
    
    # Get high-risk scenarios
    high_risk_scenarios = RiskScenarioAssessment.objects.filter(
        asset=asset,
        residual_risk_score__gt=7
    ).select_related('risk_scenario')
    
    # Get barriers with low effectiveness
    low_effectiveness_barriers = asset.barriers.annotate(
        avg_effectiveness=Avg('effectiveness_scores__overall_effectiveness_score')
    ).filter(avg_effectiveness__lt=5)
    
    # Generate recommendations
    recommendations = []
    
    # Recommendations for high-risk scenarios
    for assessment in high_risk_scenarios:
        scenario = assessment.risk_scenario
        recommendations.append({
            'priority': 'high',
            'type': 'risk_scenario',
            'title': f'High Risk Scenario: {scenario.name}',
            'description': (
                f'This scenario presents a high risk (score: {assessment.residual_risk_score}). '
                'Consider implementing additional barriers or improving existing ones.'
            ),
            'actions': [
                'Review and enhance existing barriers',
                'Consider implementing new barriers',
                'Review and update response procedures'
            ]
        })
    
    # Recommendations for low effectiveness barriers
    for barrier in low_effectiveness_barriers:
        recommendations.append({
            'priority': 'medium',
            'type': 'barrier_improvement',
            'title': f'Improve Barrier: {barrier.name}',
            'description': (
                f'This barrier shows low effectiveness (score: {barrier.avg_effectiveness}). '
                'Consider improvements to enhance its effectiveness.'
            ),
            'actions': [
                'Review barrier implementation',
                'Assess maintenance procedures',
                'Consider upgrades or replacements'
            ]
        })
    
    # Add general recommendations if needed
    if asset.vulnerability_score > 7:
        recommendations.append({
            'priority': 'high',
            'type': 'vulnerability',
            'title': 'High Asset Vulnerability',
            'description': (
                f'The asset shows high vulnerability (score: {asset.vulnerability_score}). '
                'Consider implementing additional security measures.'
            ),
            'actions': [
                'Review physical security measures',
                'Assess cybersecurity controls',
                'Update security procedures'
            ]
        })
    
    return Response({
        'success': True,
        'recommendations': recommendations,
        'summary': {
            'high_priority': len([r for r in recommendations if r['priority'] == 'high']),
            'medium_priority': len([r for r in recommendations if r['priority'] == 'medium']),
            'low_priority': len([r for r in recommendations if r['priority'] == 'low'])
        }
    })
