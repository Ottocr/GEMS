from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg
from django.utils import timezone
import json

# Import models
from .models.asset_models import Asset, AssetType, AssetVulnerabilityQuestion, AssetVulnerabilityAnswer, AssetCriticalityQuestion, AssetCriticalityAnswer
from .models.barrier_models import Barrier
from .models.geo_models import Country
from .models.risk_models import BaselineThreatAssessment, RiskType, Scenario
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models.log_models import RiskLog  # Ensure you have this import

@csrf_exempt
@login_required
def save_country_details(request):
    if request.method == 'POST':
        country = get_object_or_404(Country, company_operated=True)
        country.name = request.POST.get('name')
        country.code = request.POST.get('code')
        country.company_operated = request.POST.get('company_operated') == 'True'
        country.geo_data = request.POST.get('geo_data')
        country.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@csrf_exempt
@login_required
def save_asset(request):
    if request.method == 'POST':
        asset_id = request.POST.get('asset_id')
        if asset_id:
            asset = get_object_or_404(Asset, id=asset_id)
        else:
            asset = Asset()
        asset.name = request.POST.get('name')
        asset.description = request.POST.get('description')
        asset.latitude = request.POST.get('latitude')
        asset.longitude = request.POST.get('longitude')
        asset.asset_type_id = request.POST.get('asset_type')
        asset.country = get_object_or_404(Country, company_operated=True)
        asset.save()
        # Save many-to-many relationships
        scenarios = request.POST.getlist('scenarios')
        barriers = request.POST.getlist('barriers')
        asset.scenarios.set(scenarios)
        asset.barriers.set(barriers)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@csrf_exempt
@login_required
def delete_asset(request):
    if request.method == 'POST':
        asset_id = request.POST.get('asset_id')
        asset = get_object_or_404(Asset, id=asset_id)
        asset.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@csrf_exempt
@login_required
def save_bta(request):
    if request.method == 'POST':
        country = get_object_or_404(Country, company_operated=True)
        bta_list = BaselineThreatAssessment.objects.filter(country=country)
        for bta in bta_list:
            new_score = request.POST.get(f'bta_{bta.id}')
            if new_score:
                bta.baseline_score = new_score
                bta.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def security_manager_dashboard(request):
    countries = Country.objects.filter(company_operated=True)
    selected_country_id = request.GET.get('country_id')

    if selected_country_id:
        country = get_object_or_404(Country, id=selected_country_id)
        assets = Asset.objects.filter(country=country)
        bta_list = BaselineThreatAssessment.objects.filter(country=country)
    else:
        country = None
        assets = None
        bta_list = None

    # Other data that is not country-specific
    barriers = Barrier.objects.all()
    v_questions = AssetVulnerabilityQuestion.objects.all()
    c_questions = AssetCriticalityQuestion.objects.all()
    scenarios = Scenario.objects.all()
    asset_types = AssetType.objects.all()
    risk_types = RiskType.objects.all()

    context = {
        'countries': countries,
        'country': country,
        'assets': assets,
        'barriers': barriers,
        'bta_list': bta_list,
        'v_questions': v_questions,
        'c_questions': c_questions,
        'scenarios': scenarios,
        'asset_types': asset_types,
        'risk_types': risk_types,
    }
    return render(request, 'security_manager_dashboard.html', context)


@login_required
def dashboard(request):
    # Fetch data for Global Risk Summary
    total_countries = Country.objects.filter(company_operated=True).count()
    avg_global_risk_score = BaselineThreatAssessment.objects.aggregate(Avg('baseline_score'))['baseline_score__avg'] or 0

    # Fetch recent risk updates using the correct field 'timestamp'
    recent_updates = RiskLog.objects.order_by('-timestamp')[:5]

    # Fetch data for Interactive World Map
    countries = Country.objects.filter(company_operated=True).annotate(
        avg_bta_score=Avg('baseline_threats__baseline_score')
    )

    # Serialize country data with BTA scores for each risk group and the 'date_assessed' field
    country_data = []
    for country in countries:
        bta_scores = BaselineThreatAssessment.objects.filter(country=country).values(
            'risk_type__name', 'baseline_score', 'date_assessed'
        )

        country_dict = {
            'name': country.name,
            'avg_bta_score': country.avg_bta_score if country.avg_bta_score is not None else 0,
            'geo_data': country.geo_data,
            'bta_scores': [
                {
                    'risk_group': score['risk_type__name'],
                    'bta_score': score['baseline_score'],
                    'date_assessed': score['date_assessed'].strftime("%d-%m-%Y") if score['date_assessed'] else 'N/A'
                } for score in bta_scores
            ]
        }
        country_data.append(country_dict)

    # Fetch and serialize asset data
    assets = Asset.objects.all()
    asset_data = []
    for asset in assets:
        asset_dict = {
            'name': asset.name,
            'asset_type': asset.asset_type.name,
            'latitude': asset.latitude,
            'longitude': asset.longitude,
            'criticality_score': asset.criticality_score,
            'vulnerability_score': asset.vulnerability_score,
            'country': {
                'name': asset.country.name,
                'avg_bta_score': asset.country.baseline_threats.aggregate(Avg('baseline_score'))['baseline_score__avg'] or 0,
                'bta_scores': [
                    {
                        'risk_group': score.risk_type.name,
                        'bta_score': score.baseline_score,
                        'date_assessed': score.date_assessed.strftime("%d-%m-%Y") if score.date_assessed else 'N/A'
                    } for score in asset.country.baseline_threats.all()
                ]
            }
        }
        asset_data.append(asset_dict)

    # Fetch risk types for BTA Risk Categories
    risk_types = RiskType.objects.all()

    # Prepare context to pass to the template
    context = {
        'total_countries': total_countries,
        'avg_global_risk_score': avg_global_risk_score,
        'recent_updates': recent_updates,
        'countries': json.dumps(country_data or []),  # Ensure countries are passed as JSON data
        'assets': json.dumps(asset_data or []),  # Ensure assets are passed as JSON data
        'risk_types': risk_types,
    }

    return render(request, 'dashboard.html', context)

@login_required
def country_risk_score(request, country_id, risk_type_id):
    country = get_object_or_404(Country, id=country_id)
    risk_type = get_object_or_404(RiskType, id=risk_type_id)
    
    score = BaselineThreatAssessment.objects.filter(
        country=country,
        risk_type=risk_type
    ).aggregate(Avg('baseline_score'))['baseline_score__avg'] or 0

    return JsonResponse({'score': score})


@login_required
def country_detail(request, country_id):
    country = get_object_or_404(Country, id=country_id)
    assets = Asset.objects.filter(country=country)
    risk_types = RiskType.objects.all()
    bta_scores = BaselineThreatAssessment.objects.filter(country=country)

    context = {
        'country': country,
        'assets': assets,
        'risk_types': risk_types,
        'bta_scores': bta_scores,
    }
    return render(request, 'country.html', context)


@login_required
def asset_detail(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    context = {
        'asset': asset,
        'barriers': asset.barriers.all(),
        'scenarios': asset.scenarios.all(),
    }
    return render(request, 'asset.html', context)

@login_required
def trends(request):
    # Add logic to fetch global trend data
    context = {
        'global_trend_data': {},  # Placeholder for global trend data
    }
    return render(request, 'trends.html', context)

@login_required
def risk_matrix_generator(request):
    step = request.GET.get('step', '1')
    context = {'step': step}
    
    if step == '6':
        # Final step: generate and display the risk matrices
        asset_id = request.session.get('asset_id')
        if asset_id:
            asset = get_object_or_404(Asset, id=asset_id)
            FinalRiskMatrix.generate_matrices(asset)
            
            overall_matrices = FinalRiskMatrix.objects.filter(
                asset=asset,
                risk_type__in=RiskType.objects.all()
            )
            risk_specific_matrices = FinalRiskMatrix.objects.filter(
                asset=asset,
                risk_type__in=RiskSubtype.objects.all()
            )
            barrier_specific_matrices = FinalRiskMatrix.objects.filter(
                asset=asset,
                risk_type__in=Barrier.objects.all()
            )
            
            context['overall_matrices'] = overall_matrices
            context['risk_specific_matrices'] = risk_specific_matrices
            context['barrier_specific_matrices'] = barrier_specific_matrices
            context['asset'] = asset
        else:
            return redirect(reverse('risk_matrix_generator') + '?step=1')
    elif step == '3':
        asset_id = request.session.get('asset_id')
        if asset_id:
            context['risk_types'] = RiskType.objects.all()
        else:
            return redirect(reverse('risk_matrix_generator') + '?step=2')
    elif step == '4':
        risk_type_id = request.session.get('risk_type_id')
        if risk_type_id:
            context['scenarios'] = Scenario.objects.filter(risk_subtypes__risk_type_id=risk_type_id)
        else:
            return redirect(reverse('risk_matrix_generator') + '?step=3')
    elif step == '5':
        scenario_id = request.session.get('scenario_id')
        if scenario_id:
            scenario = get_object_or_404(Scenario, id=scenario_id)
            # Retrieve barriers linked to the risk subtypes of the scenario
            barriers = Barrier.objects.filter(risk_types__in=scenario.risk_subtypes.values_list('risk_type', flat=True)).distinct()
            context['barriers'] = barriers  # Now simply pass the barriers to the context
        else:
            return redirect(reverse('risk_matrix_generator') + '?step=4')
    
    return render(request, 'risk_matrix_generator.html', context)

@login_required
def save_step_data(request):
    if request.method == 'POST':
        step = request.POST.get('step')
        if step == '1':
            request.session['country_id'] = request.POST.get('country_id')
        elif step == '2':
            request.session['asset_id'] = request.POST.get('asset_id')
        elif step == '3':
            request.session['risk_type_id'] = request.POST.get('risk_type_id')
        elif step == '4':
            request.session['scenario_id'] = request.POST.get('scenario_id')
        elif step == '5':
            # Save barrier effectiveness and scenario assessment
            asset_id = request.session.get('asset_id')
            scenario_id = request.session.get('scenario_id')
            likelihood = request.POST.get('likelihood')
            impact = request.POST.get('impact')
            barrier_effectiveness = {}
            barrier_performance = {}
            for key, value in request.POST.items():
                if key.startswith('barrier_subtype_effectiveness_'):
                    barrier_subtype_id = key.split('_')[3]
                    barrier_effectiveness[barrier_subtype_id] = int(value)
                elif key.startswith('barrier_subtype_performance_'):
                    barrier_subtype_id = key.split('_')[3]
                    barrier_performance[barrier_subtype_id] = int(value)
            
            assessment, created = RiskScenarioAssessment.objects.update_or_create(
                asset_id=asset_id,
                risk_scenario_id=scenario_id,
                defaults={
                    'likelihood_rating': likelihood,
                    'impact_score': impact,
                    'barrier_effectiveness': barrier_effectiveness,
                    'barrier_performance': barrier_performance
                }
            )
            
            # Automatically generate risk matrix if all required data is available
            asset = get_object_or_404(Asset, id=asset_id)
            FinalRiskMatrix.generate_matrices(asset)
        
        next_step = int(step) + 1
        return JsonResponse({'success': True, 'next_step': next_step})
    return JsonResponse({'success': False}, status=400)

@login_required
def report_barrier_issue(request):
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
def resolve_barrier_issue(request, issue_id):
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
def trend_analysis(request):
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
def asset_risk_dashboard(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    overall_matrices = FinalRiskMatrix.objects.filter(
        asset=asset,
        risk_type__in=RiskType.objects.all()
    )
    risk_specific_matrices = FinalRiskMatrix.objects.filter(
        asset=asset,
        risk_type__in=RiskSubtype.objects.all()
    )
    barrier_specific_matrices = FinalRiskMatrix.objects.filter(
        asset=asset,
        risk_type__in=Barrier.objects.all()
    )
    
    context = {
        'asset': asset,
        'overall_matrices': overall_matrices,
        'risk_specific_matrices': risk_specific_matrices,
        'barrier_specific_matrices': barrier_specific_matrices,
    }
    
    return render(request, 'asset_risk_dashboard.html', context)

@login_required
def asset_link_management(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        asset_ids = request.POST.getlist('assets')
        risk_type_ids = request.POST.getlist('shared_risks')
        barrier_ids = request.POST.getlist('shared_barriers')

        asset_link = AssetLink.objects.create(name=name)
        asset_link.assets.set(asset_ids)
        asset_link.shared_risks.set(risk_type_ids)
        asset_link.shared_barriers.set(barrier_ids)

        return JsonResponse({'success': True, 'message': 'Asset link created successfully'})

    assets = Asset.objects.all()
    risk_types = RiskType.objects.all()
    barriers = Barrier.objects.all()
    asset_links = AssetLink.objects.all()

    context = {
        'assets': assets,
        'risk_types': risk_types,
        'barriers': barriers,
        'asset_links': asset_links,
    }

    return render(request, 'asset_link_management.html', context)

@login_required
def update_linked_assets(request, asset_link_id):
    asset_link = get_object_or_404(AssetLink, id=asset_link_id)
    assets = asset_link.assets.all()

    for asset in assets:
        asset.update_risk_assessment_based_on_link()

    return JsonResponse({'success': True, 'message': 'Linked assets updated successfully'})

@login_required
def countries_list_view(request):
    operated_countries = Country.objects.filter(company_operated=True)
    
    operated_countries_data = []
    for country in operated_countries:
        country_data = {
            'name': country.name,
            'code': country.code,
            'continent': country.continent.name,
            'geo_data': json.loads(country.geo_data) if country.geo_data else None
        }
        operated_countries_data.append(country_data)
    
    context = {
        'operated_countries': operated_countries,
        'operated_countries_json': json.dumps(operated_countries_data)
    }
    return render(request, 'countries_list.html', context)

@login_required
def country_detail_view(request, country_id):
    country = get_object_or_404(Country, id=country_id)
    assets = Asset.objects.filter(country=country)
    asset_types = Asset.objects.filter(country=country).values_list('asset_type__name', flat=True).distinct()
    bta_scores = BaselineThreatAssessment.objects.filter(country=country)
    
    context = {
        'country': country,
        'assets': assets,
        'asset_types': asset_types,
        'bta_scores': bta_scores,
    }
    return render(request, 'country_detail.html', context)

@login_required
def asset_detail_view(request, asset_id):
    asset = get_object_or_404(Asset, id=asset_id)
    scenarios = asset.scenario_assets.all()
    
    context = {
        'asset': asset,
        'scenarios': scenarios,
    }
    return render(request, 'asset_detail.html', context)

@login_required
def global_assets_view(request):
    assets = Asset.objects.all()
    
    assets_data = []
    for asset in assets:
        asset_data = {
            'name': asset.name,
            'asset_type': asset.asset_type.name,
            'country': asset.country.name,
            'latitude': asset.latitude,
            'longitude': asset.longitude,
        }
        assets_data.append(asset_data)
    
    context = {
        'assets': assets,
        'assets_json': json.dumps(assets_data)
    }
    return render(request, 'global_assets.html', context)
