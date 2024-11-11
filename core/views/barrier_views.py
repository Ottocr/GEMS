from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta
import json

from ..models.barrier_models import (
    Barrier, BarrierCategory, BarrierCharacteristicAssessment,
    BarrierEffectivenessScore, BarrierIssueReport, BarrierScenarioEffectiveness
)
from ..models.asset_models import Asset
from ..models.risk_models import RiskType, Scenario, FinalRiskMatrix

@login_required
def barrier_assessment_list(request):
    """Display list of barrier assessments"""
    barriers = Barrier.objects.select_related(
        'category'
    ).prefetch_related(
        'effectiveness_scores',
        'characteristic_assessments',
        'assets'
    ).annotate(
        avg_effectiveness=Avg('effectiveness_scores__overall_effectiveness_score')
    )
    
    context = {
        'barriers': barriers,
    }
    return render(request, 'barrier_assessment_list.html', context)

@login_required
def barrier_assessment(request, barrier_id):
    """Display barrier assessment form"""
    barrier = get_object_or_404(Barrier, id=barrier_id)
    asset_id = request.GET.get('asset')
    asset = get_object_or_404(Asset, id=asset_id) if asset_id else None
    
    context = {
        'barrier': barrier,
        'asset': asset,
        'characteristics': barrier.category.characteristics.all(),
        'scenarios': Scenario.objects.filter(barriers=barrier),
        'risk_types': RiskType.objects.all(),
    }
    
    return render(request, 'barrier_assessment.html', context)

@login_required
def get_barrier_assessment_form(request, barrier_id):
    """Get the assessment form for a specific barrier"""
    barrier = get_object_or_404(Barrier, id=barrier_id)
    
    # Get existing assessments
    characteristic_assessments = {
        assessment.characteristic_id: assessment.selected_value
        for assessment in barrier.characteristic_assessments.all()
    }
    
    effectiveness_scores = {
        score.risk_type_id: {
            'preventive': score.preventive_capability,
            'detection': score.detection_capability,
            'response': score.response_capability,
            'reliability': score.reliability,
            'coverage': score.coverage
        }
        for score in barrier.effectiveness_scores.all()
    }
    
    context = {
        'barrier': barrier,
        'characteristic_assessments': characteristic_assessments,
        'effectiveness_scores': effectiveness_scores
    }
    
    return render(request, 'partials/barrier_assessment_form.html', context)

@login_required
@csrf_exempt
def save_barrier_characteristics(request, barrier_id):
    """Save barrier characteristic assessments"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        with transaction.atomic():
            for char_id, value in data.get('characteristics', {}).items():
                characteristic = barrier.category.characteristics.get(id=char_id)
                score = next(
                    (item['score'] for item in characteristic.possible_values 
                     if item['value'] == value),
                    5  # Default score if no match found
                )
                BarrierCharacteristicAssessment.objects.update_or_create(
                    barrier=barrier,
                    characteristic_id=char_id,
                    defaults={
                        'selected_value': value,
                        'score': score
                    }
                )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
def save_barrier_scenarios(request, barrier_id):
    """Save barrier scenario effectiveness"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
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

@login_required
@csrf_exempt
def save_barrier_effectiveness(request, barrier_id):
    """Save barrier effectiveness scores"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        with transaction.atomic():
            for risk_type_id, scores in data.get('effectiveness', {}).items():
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
            
            barrier.update_overall_effectiveness()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_barrier_trends(request, barrier_id):
    """Get trend data for a specific barrier"""
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
    
    # Get component effectiveness
    components = []
    for assessment in barrier.characteristic_assessments.all():
        components.append({
            'name': assessment.characteristic.name,
            'score': assessment.score,
            'change': 0  # You would calculate this from historical data
        })
    
    # Get risk impacts
    risk_impacts = []
    for score in barrier.effectiveness_scores.all():
        risk_impacts.append({
            'name': score.risk_type.name,
            'reduction': score.overall_effectiveness_score
        })
    
    # Get recent issues
    issues = BarrierIssueReport.objects.filter(
        barrier=barrier,
        reported_at__gte=start_date
    ).order_by('-reported_at')
    
    # Prepare chart data
    chart_data = {
        'dates': dates,
        'effectiveness_scores': effectiveness_data,
        'component_labels': [c['name'] for c in components],
        'component_scores': [c['score'] for c in components],
        'risk_labels': [r['name'] for r in risk_impacts],
        'risk_reductions': [r['reduction'] for r in risk_impacts],
        'risk_colors': [
            '#27ae60' if r['reduction'] >= 70 else '#f1c40f' if r['reduction'] >= 40 else '#e74c3c'
            for r in risk_impacts
        ]
    }
    
    context = {
        'barrier': barrier,
        'trend_direction': trend_direction,
        'trend_percentage': trend_percentage,
        'components': components,
        'risk_impacts': risk_impacts,
        'issues': issues,
        'chart_data': chart_data
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse(chart_data)
    
    return render(request, 'partials/barrier_trends.html', context)

@login_required
@csrf_exempt
def report_barrier_issue(request):
    """Report an issue with a specific barrier"""
    if request.method == 'POST':
        barrier_id = request.POST.get('barrier_id')
        description = request.POST.get('description')
        impact_rating = request.POST.get('impact_rating')
        
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
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
@csrf_exempt
def resolve_barrier_issue(request, issue_id):
    """Resolve a reported barrier issue"""
    if request.method == 'POST':
        issue = get_object_or_404(BarrierIssueReport, id=issue_id)
        resolution_notes = request.POST.get('resolution_notes')
        
        issue.status = 'RESOLVED'
        issue.resolved_at = timezone.now()
        issue.resolution_notes = resolution_notes
        issue.save()
        
        # Trigger the update of barrier effectiveness
        issue.barrier.update_overall_effectiveness()
        issue.barrier.propagate_effectiveness()
        
        return JsonResponse({'success': True, 'message': 'Issue resolved successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'}, status=400)

@login_required
def get_barriers_by_category(request, category_id):
    """Get barriers for a specific category"""
    barriers = Barrier.objects.filter(category_id=category_id).values('id', 'name')
    return JsonResponse({'barriers': list(barriers)})
