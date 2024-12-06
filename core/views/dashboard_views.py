"""
Dashboard API Views.
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Avg, Max
import json

from ..models.asset_models import (
    Asset, AssetType, AssetVulnerabilityQuestion, AssetCriticalityQuestion
)
from ..models.barrier_models import Barrier, BarrierCategory
from ..models.geo_models import Country
from ..models.risk_models import BaselineThreatAssessment, RiskType, Scenario
from ..models.log_models import RiskLog

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_dashboard_data(request):
    """API endpoint returning global risk summary data."""
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
    recent_updates = list(RiskLog.objects.order_by('-timestamp')[:5].values())

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
            'id': asset.id,  # Added the asset ID here
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

    # Fetch risk types
    risk_types = list(RiskType.objects.values())

    return Response({
        'total_countries': total_countries,
        'avg_global_risk_score': round(avg_global_risk_score, 2),
        'recent_updates': recent_updates,
        'countries': country_data,
        'assets': asset_data,
        'risk_types': risk_types,
    })

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_security_manager_data(request):
    """API endpoint for security manager dashboard data."""
    countries = Country.objects.filter(company_operated=True)
    selected_country_id = request.GET.get('country_id')

    # Prepare countries data with GeoJSON
    countries_data = []
    for country in countries:
        country_dict = {
            'id': country.id,
            'name': country.name,
            'code': country.code,
            'geo_data': country.geo_data if isinstance(country.geo_data, dict) else json.loads(country.geo_data) if country.geo_data else None
        }
        countries_data.append(country_dict)

    response_data = {
        'countries': countries_data,
        'barriers': list(Barrier.objects.values()),
        'vulnerability_questions': list(AssetVulnerabilityQuestion.objects.values()),
        'criticality_questions': list(AssetCriticalityQuestion.objects.values()),
        'scenarios': list(Scenario.objects.values()),
        'asset_types': list(AssetType.objects.values()),
        'risk_types': list(RiskType.objects.values()),
    }

    if selected_country_id:
        try:
            country = get_object_or_404(Country, id=selected_country_id)
            assets = Asset.objects.filter(country=country)
            risk_types = RiskType.objects.all()
            
            # Create a list of BTAs
            bta_list = []
            for risk_type in risk_types:
                latest_bta = BaselineThreatAssessment.objects.filter(
                    country=country,
                    risk_type=risk_type
                ).order_by('-date_assessed').first()
                
                if latest_bta:
                    bta_list.append({
                        'country_id': country.id,
                        'risk_type_id': risk_type.id,
                        'baseline_score': latest_bta.baseline_score,
                        'impact_on_assets': latest_bta.impact_on_assets,
                        'notes': latest_bta.notes,
                        'date_assessed': latest_bta.date_assessed.strftime("%Y-%m-%d")
                    })
                else:
                    bta_list.append({
                        'country_id': country.id,
                        'risk_type_id': risk_type.id,
                        'baseline_score': 5,
                        'impact_on_assets': True,
                        'notes': '',
                        'date_assessed': None
                    })

            response_data.update({
                'selected_country': {
                    'id': country.id,
                    'name': country.name,
                    'code': country.code,
                    'geo_data': country.geo_data if isinstance(country.geo_data, dict) else json.loads(country.geo_data) if country.geo_data else None
                },
                'assets': list(assets.values()),
                'bta_list': bta_list
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    return Response(response_data)
