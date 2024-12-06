"""
Country Management API Views.
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
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

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def search_countries(request):
    """API endpoint to search for non-operated countries."""
    query = request.GET.get('query', '').strip()
    if len(query) < 2:
        return Response({'countries': []})
    
    countries = Country.objects.filter(
        Q(name__icontains=query) | Q(code__icontains=query),
        company_operated=False
    ).values('id', 'name')[:10]
    
    return Response({'countries': list(countries)})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def add_operated_country(request):
    """API endpoint to mark a country as operated."""
    try:
        country_id = request.data.get('country_id')
        country = get_object_or_404(Country, id=country_id)
        
        if country.company_operated:
            return Response({
                'success': False,
                'error': 'Country is already marked as operated'
            })
        
        country.company_operated = True
        country.save()
        
        logger.info(f"Added operated country: {country.name} (ID: {country.id})")
        return Response({'success': True})
        
    except Exception as e:
        logger.error(f"Error adding operated country: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=400)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def remove_operated_country(request):
    """API endpoint to remove country from operated list."""
    try:
        country_id = request.data.get('country_id')
        country = get_object_or_404(Country, id=country_id)
        
        if not country.company_operated:
            return Response({
                'success': False,
                'error': 'Country is not marked as operated'
            })
        
        country.company_operated = False
        country.save()
        
        logger.info(f"Removed operated country: {country.name} (ID: {country.id})")
        return Response({'success': True})
        
    except Exception as e:
        logger.error(f"Error removing operated country: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=400)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_country_geojson(request, country_id):
    """API endpoint to get GeoJSON data for a specific country."""
    try:
        country = get_object_or_404(Country, id=country_id)
        if not country.geo_data:
            return Response({
                'success': False,
                'error': 'No GeoJSON data available for this country'
            })
        
        return Response({
            'success': True,
            'geojson': country.geo_data
        })
        
    except Exception as e:
        logger.error(f"Error getting country GeoJSON: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=400)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_operated_countries_geojson(request):
    """API endpoint to get GeoJSON data for all operated countries."""
    try:
        countries = Country.objects.filter(company_operated=True)
        features = []
        
        for country in countries:
            if country.geo_data:
                # Parse the stored GeoJSON data
                geo_data = country.geo_data
                if isinstance(geo_data, str):
                    geo_data = json.loads(geo_data)
                
                # If geo_data is just a geometry, wrap it in a Feature
                if 'type' in geo_data and geo_data['type'] in ['MultiPolygon', 'Polygon']:
                    feature = {
                        'type': 'Feature',
                        'geometry': geo_data,
                        'properties': {
                            'id': country.id,
                            'name': country.name,
                            'code': country.code
                        }
                    }
                    features.append(feature)
                # If geo_data is already a Feature or FeatureCollection
                elif 'features' in geo_data:
                    for feature in geo_data['features']:
                        if 'properties' not in feature:
                            feature['properties'] = {}
                        feature['properties'].update({
                            'id': country.id,
                            'name': country.name,
                            'code': country.code
                        })
                        features.append(feature)
                elif geo_data.get('type') == 'Feature':
                    if 'properties' not in geo_data:
                        geo_data['properties'] = {}
                    geo_data['properties'].update({
                        'id': country.id,
                        'name': country.name,
                        'code': country.code
                    })
                    features.append(geo_data)
        
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        return Response({
            'success': True,
            'geojson': geojson
        })
        
    except Exception as e:
        logger.error(f"Error getting operated countries GeoJSON: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=400)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def save_country_details(request):
    """API endpoint to save or update country details."""
    try:
        data = request.data
        country_id = data.get('country_id')
        name = data.get('name')
        code = data.get('code')
        company_operated = data.get('company_operated') == 'True'
        geo_data = data.get('geo_data')

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

        return Response({'success': True, 'country_id': country.id})
    except Exception as e:
        logger.error(f"Error saving country details: {str(e)}")
        return Response({'success': False, 'error': str(e)}, status=400)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@transaction.atomic
def save_bta(request):
    """API endpoint to save Baseline Threat Assessment scores."""
    try:
        # Log raw request data
        logger.debug("Request data: %s", dict(request.data))
        
        country_id = request.data.get('country_id')
        if not country_id:
            logger.error("No country_id provided in request data")
            return Response({'success': False, 'error': 'Country ID is required'}, status=400)
            
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
            
            score = request.data.get(score_key)
            impact_on_assets = request.data.get(impact_key) == 'on'
            notes = request.data.get(notes_key, '')
            
            logger.debug("Processing risk type %s (ID: %s):", risk_type.name, risk_type.id)
            logger.debug("- Score key: %s, Value: %s", score_key, score)
            logger.debug("- Impact key: %s, Value: %s", impact_key, request.data.get(impact_key))
            logger.debug("- Notes key: %s, Value: %s", notes_key, notes)
            
            if score:
                try:
                    score = float(score)
                    if score < 1 or score > 10:
                        logger.error("Invalid score value for %s: %s", risk_type.name, score)
                        return Response({
                            'success': False,
                            'error': f'Score must be between 1 and 10 for {risk_type.name}'
                        }, status=400)
                    
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
                    return Response({
                        'success': False,
                        'error': f'Invalid score value for {risk_type.name}'
                    }, status=400)
                except Exception as e:
                    logger.error("Error saving BTA for %s: %s", risk_type.name, str(e))
                    return Response({
                        'success': False,
                        'error': f'Error saving BTA for {risk_type.name}: {str(e)}'
                    }, status=400)
        
        if not updated_scores:
            logger.error("No valid BTA scores provided in request")
            return Response({
                'success': False,
                'error': 'No valid BTA scores provided'
            }, status=400)
        
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
        return Response({
            'success': True,
            'scores': updated_scores,
            'message': 'BTA scores updated successfully'
        })
        
    except Country.DoesNotExist:
        logger.error("Country not found: ID %s", country_id)
        return Response({
            'success': False,
            'error': 'Country not found'
        }, status=404)
    except Exception as e:
        logger.error("Unexpected error saving BTAs: %s", str(e), exc_info=True)
        return Response({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)
