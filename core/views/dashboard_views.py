"""
Dashboard Views.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max
import json

from ..models.asset_models import (
    Asset, AssetType, AssetVulnerabilityQuestion, AssetCriticalityQuestion
)
from ..models.barrier_models import Barrier, BarrierCategory
from ..models.geo_models import Country
from ..models.risk_models import BaselineThreatAssessment, RiskType, Scenario
from ..models.log_models import RiskLog

@login_required
def dashboard(request):
    """Main dashboard view showing global risk summary."""
    # Previous dashboard code remains the same...
    total_countries = Country.objects.filter(company_operated=True).count()
    
    # Get the latest BTA scores for global risk average
    latest_bta_dates = BaselineThreatAssessment.objects.values(
        'country', 'risk_type'
    ).annotate(
        latest_date=Max('date_assessed')
    )
    
    latest_bta_scores = []
    for date_info in latest_bta_dates:
        bta = BaselineThreatAssessment.objects.get(
            country_id=date_info['country'],
            risk_type_id=date_info['risk_type'],
            date_assessed=date_info['latest_date']
        )
        latest_bta_scores.append(bta.baseline_score)
    
    avg_global_risk_score = sum(latest_bta_scores) / len(latest_bta_scores) if latest_bta_scores else 0

    # Fetch recent risk updates
    recent_updates = RiskLog.objects.order_by('-timestamp')[:5]

    # Fetch data for Interactive World Map
    countries = Country.objects.filter(company_operated=True)

    # Serialize country data
    country_data = []
    for country in countries:
        # Get latest BTA scores for each risk type
        latest_dates = BaselineThreatAssessment.objects.filter(
            country=country
        ).values('risk_type').annotate(latest_date=Max('date_assessed'))
        
        bta_scores = []
        for date_info in latest_dates:
            bta = BaselineThreatAssessment.objects.get(
                country=country,
                risk_type_id=date_info['risk_type'],
                date_assessed=date_info['latest_date']
            )
            bta_scores.append({
                'risk_group': bta.risk_type.name,
                'bta_score': bta.baseline_score,
                'date_assessed': bta.date_assessed.strftime("%d-%m-%Y")
            })

        country_dict = {
            'name': country.name,
            'avg_bta_score': sum(score['bta_score'] for score in bta_scores) / len(bta_scores) if bta_scores else 0,
            'geo_data': country.geo_data,
            'bta_scores': bta_scores
        }
        country_data.append(country_dict)

    # Fetch and serialize asset data
    assets = Asset.objects.all()
    asset_data = []
    for asset in assets:
        # Get latest BTA scores for the asset's country
        latest_dates = BaselineThreatAssessment.objects.filter(
            country=asset.country
        ).values('risk_type').annotate(latest_date=Max('date_assessed'))
        
        country_bta_scores = []
        for date_info in latest_dates:
            bta = BaselineThreatAssessment.objects.get(
                country=asset.country,
                risk_type_id=date_info['risk_type'],
                date_assessed=date_info['latest_date']
            )
            country_bta_scores.append({
                'risk_group': bta.risk_type.name,
                'bta_score': bta.baseline_score,
                'date_assessed': bta.date_assessed.strftime("%d-%m-%Y")
            })

        asset_dict = {
            'name': asset.name,
            'asset_type': asset.asset_type.name,
            'latitude': asset.latitude,
            'longitude': asset.longitude,
            'criticality_score': asset.criticality_score,
            'vulnerability_score': asset.vulnerability_score,
            'country': {
                'name': asset.country.name,
                'avg_bta_score': sum(score['bta_score'] for score in country_bta_scores) / len(country_bta_scores) if country_bta_scores else 0,
                'bta_scores': country_bta_scores
            }
        }
        asset_data.append(asset_dict)

    # Fetch risk types for BTA Risk Categories
    risk_types = RiskType.objects.all()

    context = {
        'total_countries': total_countries,
        'avg_global_risk_score': round(avg_global_risk_score, 2),
        'recent_updates': recent_updates,
        'countries': json.dumps(country_data or []),
        'assets': json.dumps(asset_data or []),
        'risk_types': risk_types,
    }

    return render(request, 'dashboard.html', context)

@login_required
def security_manager_dashboard(request):
    """Dashboard for security managers to manage assets and barriers."""
    countries = Country.objects.filter(company_operated=True)
    selected_country_id = request.GET.get('country_id')

    if selected_country_id:
        country = get_object_or_404(Country, id=selected_country_id)
        assets = Asset.objects.filter(country=country)
        
        # Get all risk types
        risk_types = RiskType.objects.all()
        
        # Create a list of BTAs, using the latest BTA for each risk type if it exists
        bta_list = []
        for risk_type in risk_types:
            # Try to get the latest BTA for this risk type
            latest_bta = BaselineThreatAssessment.objects.filter(
                country=country,
                risk_type=risk_type
            ).order_by('-date_assessed').first()
            
            if latest_bta:
                # Use existing BTA
                bta_list.append(latest_bta)
            else:
                # Create a dummy BTA object (not saved to database)
                bta = BaselineThreatAssessment(
                    country=country,
                    risk_type=risk_type,
                    baseline_score=5,  # Default score
                    impact_on_assets=True,  # Default impact
                    notes=''  # Empty notes
                )
                bta_list.append(bta)
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
        'selected_country_id': selected_country_id,
    }
    return render(request, 'security_manager_dashboard.html', context)
