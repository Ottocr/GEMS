"""
Analysis Views.

This module contains views for analyzing risk data and generating recommendations.
It provides trend analysis, risk insights, and actionable recommendations based on
risk assessments, barrier effectiveness, and historical data.

Main components:
- Trend analysis across different time periods
- Risk level tracking and visualization
- Barrier effectiveness analysis
- Recommendation generation based on risk levels
- Historical data comparison

The analysis views help users understand risk trends and make informed decisions
about risk mitigation strategies. They combine data from multiple sources to
provide meaningful insights and practical recommendations.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta

from ..models.asset_models import Asset
from ..models.barrier_models import Barrier
from ..models.risk_models import RiskType, RiskScenarioAssessment
from ..models.log_models import RiskLog

@login_required
def trend_analysis(request):
    """Perform trend analysis on risk assessments.
    
    Analyzes:
    - Risk score trends over time
    - BTA score changes
    - Vulnerability score progression
    - Criticality score changes
    - Barrier effectiveness trends
    
    Time periods:
    - Last 30 days (default)
    - Custom timeframe specified in request
    
    The analysis helps identify patterns and changes in risk levels
    over time, supporting informed decision-making about risk
    mitigation strategies.
    """
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
    
    data = {
        'labels': [log.timestamp.strftime('%Y-%m-%d') for log in risk_logs],
        'bta_scores': [log.bta_score for log in risk_logs],
        'vulnerability_scores': [log.vulnerability_score for log in risk_logs],
        'criticality_scores': [log.criticality_score for log in risk_logs],
        'residual_risk_scores': [log.residual_risk_score for log in risk_logs],
    }
    
    context = {
        'asset': asset,
        'risk_type': risk_type,
        'data': data,
        'timeframe': timeframe,
    }
    
    return render(request, 'trend_analysis.html', context)

@login_required
def get_recommendations(request, asset_id):
    """Generate recommendations based on risk assessment.
    
    Analyzes:
    - High-risk scenarios (score > 7)
    - Low effectiveness barriers (score < 5)
    - High vulnerability areas (score > 7)
    
    Generates recommendations in three categories:
    1. High Priority: Immediate action needed
       - High-risk scenarios
       - Critical vulnerabilities
    
    2. Medium Priority: Action required
       - Barrier improvements
       - Moderate risk scenarios
    
    3. Low Priority: Monitor and review
       - Minor improvements
       - Maintenance tasks
    
    Each recommendation includes:
    - Priority level
    - Type (risk_scenario, barrier_improvement, vulnerability)
    - Title and description
    - Specific actions to take
    
    The recommendations are practical and actionable, helping users
    focus on the most critical areas for risk reduction.
    """
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
    
    return JsonResponse({
        'success': True,
        'recommendations': recommendations,
        'summary': {
            'high_priority': len([r for r in recommendations if r['priority'] == 'high']),
            'medium_priority': len([r for r in recommendations if r['priority'] == 'medium']),
            'low_priority': len([r for r in recommendations if r['priority'] == 'low'])
        }
    })
