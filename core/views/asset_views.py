"""
Asset Management API Views.

This module contains API endpoints related to asset management, including creation, updating,
and viewing of assets and their associated barriers. Assets are the core entities
that are assessed for risks and protected by barriers.

Main components:
- Asset CRUD operations
- Asset-barrier associations
- Asset linking for shared risks
- Asset data retrieval
"""

from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger('core')

from ..models.asset_models import (
    Asset, AssetType, AssetVulnerabilityAnswer,
    AssetCriticalityAnswer, AssetLink
)
from ..models.geo_models import Country
from ..models.barrier_models import (
    Barrier, BarrierEffectivenessScore, BarrierCategory
)
from ..models.risk_models import RiskType, Scenario, FinalRiskMatrix

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_global_assets(request):
    """API endpoint to get all assets data."""
    assets = Asset.objects.all()
    
    assets_data = []
    for asset in assets:
        assets_data.append({
            'id': asset.id,
            'name': asset.name,
            'asset_type': asset.asset_type.name,
            'country': asset.country.name,
            'latitude': asset.latitude,
            'longitude': asset.longitude,
            'criticality_score': asset.criticality_score,
            'vulnerability_score': asset.vulnerability_score
        })
    
    return Response({'assets': assets_data})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_asset_details(request, asset_id):
    """API endpoint to get detailed information about a specific asset."""
    asset = get_object_or_404(Asset, id=asset_id)
    scenarios = asset.scenarios.all()
    
    asset_data = {
        'id': asset.id,
        'name': asset.name,
        'asset_type': asset.asset_type.name,
        'description': asset.description,
        'country': asset.country.name,
        'latitude': asset.latitude,
        'longitude': asset.longitude,
        'criticality_score': asset.criticality_score,
        'vulnerability_score': asset.vulnerability_score,
        'scenarios': list(scenarios.values('id', 'name', 'description')),
        'barriers': list(asset.barriers.values('id', 'name', 'category__name'))
    }
    
    return Response({'asset': asset_data})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_asset_risk_data(request, asset_id):
    """API endpoint to get risk data for a specific asset."""
    asset = get_object_or_404(Asset, id=asset_id)
    risk_types = RiskType.objects.all()
    
    matrices_data = {
        'overall': list(FinalRiskMatrix.objects.filter(
            asset=asset,
            risk_type__in=risk_types
        ).values()),
        'risk_specific': list(FinalRiskMatrix.objects.filter(
            asset=asset,
            risk_type__in=risk_types
        ).values()),
        'barrier_specific': list(FinalRiskMatrix.objects.filter(
            asset=asset,
            risk_type__in=risk_types
        ).values())
    }
    
    return Response({'matrices': matrices_data})

@api_view(['GET', 'POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def manage_asset_links(request):
    """API endpoint to manage asset links for shared risks and barriers."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            asset_ids = data.get('assets', [])
            risk_type_ids = data.get('shared_risks', [])
            barrier_ids = data.get('shared_barriers', [])

            asset_link = AssetLink.objects.create(name=name)
            asset_link.assets.set(asset_ids)
            asset_link.shared_risks.set(risk_type_ids)
            asset_link.shared_barriers.set(barrier_ids)

            return Response({'success': True, 'message': 'Asset link created successfully'})
        except Exception as e:
            return Response({'success': False, 'error': str(e)})
    else:
        # GET request - return available data for creating links
        return Response({
            'assets': list(Asset.objects.values('id', 'name')),
            'risk_types': list(RiskType.objects.values('id', 'name')),
            'barriers': list(Barrier.objects.values('id', 'name')),
            'asset_links': list(AssetLink.objects.values('id', 'name'))
        })

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def update_linked_assets(request, asset_link_id):
    """API endpoint to update all assets linked via a specific asset link."""
    try:
        asset_link = get_object_or_404(AssetLink, id=asset_link_id)
        assets = asset_link.assets.all()

        for asset in assets:
            asset.update_risk_assessment_based_on_link()

        return Response({'success': True, 'message': 'Linked assets updated successfully'})
    except Exception as e:
        return Response({'success': False, 'error': str(e)})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def save_asset(request):
    """API endpoint to save or update asset details."""
    try:
        data = request.data
        asset_id = data.get('asset_id')
        
        asset_data = {
            'name': data.get('name'),
            'asset_type_id': data.get('asset_type'),
            'description': data.get('description'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
        }
        
        with transaction.atomic():
            if asset_id:
                asset = get_object_or_404(Asset, id=asset_id)
                for key, value in asset_data.items():
                    setattr(asset, key, value)
                asset.save()
            else:
                country_id = data.get('country_id')
                country = get_object_or_404(Country, id=country_id)
                asset = Asset.objects.create(country=country, **asset_data)
            
            # Handle barriers
            barrier_ids = data.get('barriers', [])
            if barrier_ids:
                asset.barriers.set(barrier_ids)
            
            # Handle scenarios
            scenario_ids = data.get('scenarios', [])
            if scenario_ids:
                asset.scenarios.set(scenario_ids)
        
        return Response({'success': True, 'asset_id': asset.id})
    except Exception as e:
        return Response({'success': False, 'error': str(e)})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def delete_asset(request):
    """API endpoint to delete an asset."""
    try:
        data = request.data
        asset_id = data.get('asset_id')
        asset = get_object_or_404(Asset, id=asset_id)
        asset.delete()
        return Response({'success': True})
    except Exception as e:
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_asset_form_data(request, asset_id=None):
    """API endpoint to get data needed for asset form."""
    try:
        asset = None
        if asset_id:
            asset = get_object_or_404(Asset, id=asset_id)
            asset_data = {
                'id': asset.id,
                'name': asset.name,
                'asset_type_id': asset.asset_type_id,
                'description': asset.description,
                'country_id': asset.country_id,
                'latitude': asset.latitude,
                'longitude': asset.longitude,
                'barriers': list(asset.barriers.values_list('id', flat=True)),
                'scenarios': list(asset.scenarios.values_list('id', flat=True)),
                'criticality_answers': list(asset.asset_criticality_answers.values(
                    'id', 'question__question_text', 'selected_choice', 'selected_score'
                )),
                'vulnerability_answers': list(asset.asset_vulnerability_answers.values(
                    'id', 'question__question_text', 'selected_choice', 'selected_score'
                ))
            }
        else:
            asset_data = None

        return Response({
            'asset': asset_data,
            'asset_types': list(AssetType.objects.values('id', 'name')),
            'countries': list(Country.objects.filter(company_operated=True).values('id', 'name')),
            'barriers': list(Barrier.objects.values('id', 'name')),
            'scenarios': list(Scenario.objects.values('id', 'name'))
        })
    except Exception as e:
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_asset_barriers(request, asset_id):
    """API endpoint to get barriers for a specific asset."""
    try:
        asset = get_object_or_404(Asset, id=asset_id)
        logger.debug(f"Found asset: {asset.name} (ID: {asset.id})")
        
        # Get all barrier categories with their barriers
        categories = BarrierCategory.objects.prefetch_related('category_barriers').all()
        logger.debug(f"Found {categories.count()} barrier categories")
        
        categories_data = []
        for category in categories:
            barriers = category.category_barriers.all()
            logger.debug(f"Category {category.name} has {barriers.count()} barriers")
            
            categories_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'barriers': list(barriers.values('id', 'name', 'description'))
            })

        # Get asset's barriers with detailed information
        barriers = asset.barriers.all().select_related('category').prefetch_related(
            'effectiveness_scores',
            'questions',
            'risk_types',
            'risk_subtypes'
        )
        logger.debug(f"Asset has {barriers.count()} barriers")
        
        barriers_data = []
        for barrier in barriers:
            logger.debug(f"Processing barrier: {barrier.name} (ID: {barrier.id})")
            effectiveness_scores = {}
            scores = barrier.effectiveness_scores.all()
            logger.debug(f"Barrier has {scores.count()} effectiveness scores")
            
            for score in scores:
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

            risk_types = barrier.risk_types.all()
            risk_subtypes = barrier.risk_subtypes.all()
            questions = barrier.questions.all()
            
            logger.debug(f"Barrier has {risk_types.count()} risk types, {risk_subtypes.count()} subtypes, {questions.count()} questions")

            barrier_data = {
                'id': barrier.id,
                'name': barrier.name,
                'category': {
                    'id': barrier.category.id,
                    'name': barrier.category.name
                },
                'description': barrier.description,
                'effectiveness_scores': effectiveness_scores,
                'risk_types': [{'id': rt.id, 'name': rt.name} for rt in risk_types],
                'risk_subtypes': [
                    {
                        'id': rs.id,
                        'name': rs.name,
                        'risk_type': {
                            'id': rs.risk_type.id,
                            'name': rs.risk_type.name
                        }
                    }
                    for rs in risk_subtypes
                ],
                'questions': list(questions.values(
                    'id',
                    'question_text',
                    'risk_types__name',
                    'risk_subtypes__name',
                    'scenario__name',
                    'answer_choices'
                ))
            }
            barriers_data.append(barrier_data)
        
        response_data = {
            'barrier_categories': categories_data,
            'barriers': barriers_data,
            'total_barriers': len(barriers_data),
            'total_categories': len(categories_data)
        }
        logger.debug(f"Final response data: {response_data}")
        
        return Response(response_data)
    except Exception as e:
        logger.error(f"Error in get_asset_barriers: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': str(e)})

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def get_asset_barriers_list(request, asset_id):
    """API endpoint to get a simple list of barriers for a specific asset."""
    try:
        asset = get_object_or_404(Asset, id=asset_id)
        barriers = asset.barriers.all().values('id', 'name')
        return Response({'barriers': list(barriers)})
    except Exception as e:
        return Response({'success': False, 'error': str(e)})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def add_asset_barrier(request):
    """API endpoint to add a barrier to an asset."""
    try:
        data = request.data
        asset_id = data.get('asset_id')
        barrier_id = data.get('barrier_id')
        
        asset = get_object_or_404(Asset, id=asset_id)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        # Check if barrier is already assigned
        if barrier in asset.barriers.all():
            return Response({
                'success': False,
                'error': 'This barrier is already assigned to the asset'
            })
        
        # Add barrier to asset
        asset.barriers.add(barrier)
        
        # Create initial effectiveness scores for all risk types
        for risk_type in RiskType.objects.all():
            BarrierEffectivenessScore.objects.get_or_create(
                barrier=barrier,
                risk_type=risk_type,
                defaults={
                    'preventive_capability': 5,
                    'detection_capability': 5,
                    'response_capability': 5,
                    'reliability': 5,
                    'coverage': 5
                }
            )
        
        return Response({'success': True})
    except Exception as e:
        return Response({'success': False, 'error': str(e)})

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
@csrf_exempt
def remove_asset_barrier(request):
    """API endpoint to remove a barrier from an asset."""
    try:
        data = request.data
        asset_id = data.get('asset_id')
        barrier_id = data.get('barrier_id')
        
        asset = get_object_or_404(Asset, id=asset_id)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        # Remove barrier from asset
        asset.barriers.remove(barrier)
        
        # Update risk matrices
        FinalRiskMatrix.generate_matrices(asset)
        
        return Response({'success': True})
    except Exception as e:
        return Response({'success': False, 'error': str(e)})
