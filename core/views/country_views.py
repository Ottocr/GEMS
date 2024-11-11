"""
Country Management Views.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
import json
import logging

# Set up logger
logger = logging.getLogger(__name__)

from ..models.geo_models import Country
from ..models.asset_models import Asset
from ..models.risk_models import (
    BaselineThreatAssessment,
    RiskType,
    FinalRiskMatrix
)

@login_required
def search_countries(request):
    """Search for non-operated countries."""
    query = request.GET.get('query', '').strip()
    if len(query) < 2:
        return JsonResponse({'countries': []})
    
    countries = Country.objects.filter(
        Q(name__icontains=query) | Q(code__icontains=query),
        company_operated=False
    ).values('id', 'name')[:10]
    
    return JsonResponse({'countries': list(countries)})

@login_required
@transaction.atomic
def add_operated_country(request):
    """Mark a country as operated."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        country_id = request.POST.get('country_id')
        country = get_object_or_404(Country, id=country_id)
        
        if country.company_operated:
            return JsonResponse({
                'success': False,
                'error': 'Country is already marked as operated'
            })
        
        country.company_operated = True
        country.save()
        
        logger.info(f"Added operated country: {country.name} (ID: {country.id})")
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error adding operated country: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@transaction.atomic
def remove_operated_country(request):
    """Remove country from operated list."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        country_id = request.POST.get('country_id')
        country = get_object_or_404(Country, id=country_id)
        
        if not country.company_operated:
            return JsonResponse({
                'success': False,
                'error': 'Country is not marked as operated'
            })
        
        country.company_operated = False
        country.save()
        
        logger.info(f"Removed operated country: {country.name} (ID: {country.id})")
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error removing operated country: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_country_geojson(request, country_id):
    """Get GeoJSON data for a specific country."""
    try:
        country = get_object_or_404(Country, id=country_id)
        if not country.geo_data:
            return JsonResponse({
                'success': False,
                'error': 'No GeoJSON data available for this country'
            })
        
        return JsonResponse({
            'success': True,
            'geojson': country.geo_data
        })
        
    except Exception as e:
        logger.error(f"Error getting country GeoJSON: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_operated_countries_geojson(request):
    """Get GeoJSON data for all operated countries."""
    try:
        countries = Country.objects.filter(company_operated=True)
        features = []
        
        for country in countries:
            if country.geo_data:
                # Add country ID to properties for click handling
                geo_data = country.geo_data
                if isinstance(geo_data, str):
                    geo_data = json.loads(geo_data)
                
                if 'features' in geo_data:
                    for feature in geo_data['features']:
                        if 'properties' not in feature:
                            feature['properties'] = {}
                        feature['properties']['id'] = country.id
                        features.extend([feature])
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return JsonResponse({
            'success': True,
            'geojson': geojson
        })
        
    except Exception as e:
        logger.error(f"Error getting operated countries GeoJSON: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def save_country_details(request):
    """Save or update country details."""
    if request.method == 'POST':
        try:
            country_id = request.POST.get('country_id')
            name = request.POST.get('name')
            code = request.POST.get('code')
            company_operated = request.POST.get('company_operated') == 'True'
            geo_data = request.POST.get('geo_data')

            if country_id:
                country = get_object_or_404(Country, id=country_id)
                country.name = name
                country.code = code
                country.company_operated = company_operated
                country.geo_data = geo_data
                country.save()
                logger.info(f"Updated country: {name} (ID: {country_id})")
            else:
                country = Country.objects.create(
                    name=name,
                    code=code,
                    company_operated=company_operated,
                    geo_data=geo_data
                )
                logger.info(f"Created new country: {name}")

            return JsonResponse({'success': True, 'country_id': country.id})
        except Exception as e:
            logger.error(f"Error saving country details: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def countries_list_view(request):
    """Redirect to security manager dashboard."""
    return redirect('security_manager_dashboard')

@login_required
def country_detail_view(request, country_id):
    """Redirect to security manager dashboard with country selected."""
    return redirect(f'/security-manager/?country_id={country_id}')

@login_required
@transaction.atomic
def save_bta(request):
    """Save Baseline Threat Assessment scores."""
    if request.method != 'POST':
        logger.error("Invalid method: %s", request.method)
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        # Log raw request data
        logger.debug("Request POST data: %s", dict(request.POST))
        
        country_id = request.POST.get('country_id')
        if not country_id:
            logger.error("No country_id provided in POST data")
            return JsonResponse({'success': False, 'error': 'Country ID is required'})
            
        country = get_object_or_404(Country, id=country_id)
        logger.info("Processing BTAs for country: %s (ID: %s)", country.name, country_id)
        
        current_date = timezone.now().date()
        updated_scores = []
        
        # Get all risk types
        risk_types = RiskType.objects.all()
        logger.debug("Found %d risk types", risk_types.count())
        
        # Process each risk type
        for risk_type in risk_types:
            score_key = f'bta_{risk_type.id}_score'
            impact_key = f'bta_{risk_type.id}_impact'
            notes_key = f'bta_{risk_type.id}_notes'
            
            score = request.POST.get(score_key)
            impact_on_assets = request.POST.get(impact_key) == 'on'
            notes = request.POST.get(notes_key, '')
            
            logger.debug("Processing risk type %s (ID: %s):", risk_type.name, risk_type.id)
            logger.debug("- Score key: %s, Value: %s", score_key, score)
            logger.debug("- Impact key: %s, Value: %s", impact_key, request.POST.get(impact_key))
            logger.debug("- Notes key: %s, Value: %s", notes_key, notes)
            
            if score:
                try:
                    score = float(score)
                    if score < 1 or score > 10:
                        logger.error("Invalid score value for %s: %s", risk_type.name, score)
                        return JsonResponse({
                            'success': False,
                            'error': f'Score must be between 1 and 10 for {risk_type.name}'
                        })
                    
                    # Try to get existing BTA for today
                    bta = BaselineThreatAssessment.objects.filter(
                        country=country,
                        risk_type=risk_type,
                        date_assessed=current_date
                    ).first()
                    
                    if bta:
                        # Update existing BTA
                        logger.info("Updating existing BTA for %s with score %s", risk_type.name, score)
                        bta.baseline_score = score
                        bta.impact_on_assets = impact_on_assets
                        bta.notes = notes
                        bta.save()
                    else:
                        # Create new BTA
                        logger.info("Creating new BTA for %s with score %s", risk_type.name, score)
                        bta = BaselineThreatAssessment.objects.create(
                            country=country,
                            risk_type=risk_type,
                            baseline_score=score,
                            impact_on_assets=impact_on_assets,
                            notes=notes,
                            date_assessed=current_date
                        )
                    
                    logger.debug("BTA saved successfully: %s", bta)
                    
                    updated_scores.append({
                        'risk_type_id': risk_type.id,
                        'score': score,
                        'impact_on_assets': impact_on_assets,
                        'notes': notes,
                        'date_assessed': current_date.strftime('%d %b %Y')
                    })
                    
                except ValueError as e:
                    logger.error("ValueError processing score for %s: %s", risk_type.name, str(e))
                    return JsonResponse({
                        'success': False,
                        'error': f'Invalid score value for {risk_type.name}'
                    })
                except Exception as e:
                    logger.error("Error saving BTA for %s: %s", risk_type.name, str(e))
                    return JsonResponse({
                        'success': False,
                        'error': f'Error saving BTA for {risk_type.name}: {str(e)}'
                    })
        
        if not updated_scores:
            logger.error("No valid BTA scores provided in request")
            return JsonResponse({
                'success': False,
                'error': 'No valid BTA scores provided'
            })
        
        # Update risk matrices
        logger.info("Updating risk matrices for country %s", country.name)
        assets = Asset.objects.filter(country=country)
        for asset in assets:
            try:
                FinalRiskMatrix.generate_matrices(asset)
                logger.debug("Generated risk matrices for asset %s", asset.name)
            except Exception as e:
                logger.error("Error generating risk matrices for asset %s: %s", asset.name, str(e))
        
        logger.info("Successfully saved %d BTAs for country %s", len(updated_scores), country.name)
        return JsonResponse({
            'success': True,
            'scores': updated_scores,
            'message': 'BTA scores updated successfully'
        })
        
    except Country.DoesNotExist:
        logger.error("Country not found: ID %s", country_id)
        return JsonResponse({
            'success': False,
            'error': 'Country not found'
        })
    except Exception as e:
        logger.error("Unexpected error saving BTAs: %s", str(e), exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        })
