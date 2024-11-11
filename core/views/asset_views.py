"""
Asset Management Views.

This module contains views related to asset management, including creation, updating,
and viewing of assets and their associated barriers. Assets are the core entities
that are assessed for risks and protected by barriers.

Main components:
- Asset CRUD operations
- Asset-barrier associations
- Asset linking for shared risks
- Asset risk dashboard
- Asset detail views

The asset views form the core of the risk management system, as assets are the
entities being protected and assessed for risks. Assets can be linked to share
barriers and risk assessments, and their risk levels are calculated based on
various factors including BTAs, barriers, and vulnerability assessments.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import json

from ..models.asset_models import (
    Asset, AssetType, AssetVulnerabilityAnswer,
    AssetCriticalityAnswer, AssetLink
)
from ..models.geo_models import Country
from ..models.barrier_models import (
    Barrier, BarrierEffectivenessScore, BarrierCategory
)
from ..models.risk_models import RiskType, Scenario, FinalRiskMatrix

@login_required
def global_assets_view(request):
    """Display a global view of all assets.
    
    Shows:
    - Interactive map with asset locations
    - Asset list with key information
    - Risk level indicators
    - Quick access to asset management functions
    
    The view provides a high-level overview of all assets
    and their current risk status.
    """
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

@login_required
def asset_detail_view(request, asset_id):
    """Display detailed information about a specific asset.
    
    Shows:
    - Asset details and location
    - Associated barriers and their effectiveness
    - Risk scenarios affecting the asset
    - Current risk levels
    - Historical risk data
    """
    asset = get_object_or_404(Asset, id=asset_id)
    scenarios = asset.scenario_assets.all()
    
    context = {
        'asset': asset,
        'scenarios': scenarios,
    }
    return render(request, 'asset_detail.html', context)

@login_required
def asset_risk_dashboard(request, asset_id):
    """Display the risk dashboard for a specific asset.
    
    Shows:
    - Overall risk matrices
    - Risk-specific matrices
    - Barrier-specific matrices
    - Risk trends and analysis
    - Recommendations for risk reduction
    """
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
    """Manage asset links for shared risks and barriers.
    
    Allows:
    - Creating groups of related assets
    - Sharing barriers between assets
    - Applying common risk assessments
    - Managing shared risk scenarios
    
    Asset links help reduce duplicate work when multiple assets
    share similar risk profiles or protection measures.
    """
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
    """Update all assets linked via a specific asset link.
    
    Propagates:
    - Barrier effectiveness scores
    - Risk assessments
    - Scenario evaluations
    
    This ensures all linked assets maintain consistent
    risk assessments and barrier configurations.
    """
    asset_link = get_object_or_404(AssetLink, id=asset_link_id)
    assets = asset_link.assets.all()

    for asset in assets:
        asset.update_risk_assessment_based_on_link()

    return JsonResponse({'success': True, 'message': 'Linked assets updated successfully'})

@login_required
@csrf_exempt
def save_asset(request):
    """Save or update asset details.
    
    Handles:
    - Basic asset information
    - Location data
    - Asset type assignment
    - Country association
    - Barrier assignments
    - Scenario associations
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
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
        
        return JsonResponse({'success': True, 'asset_id': asset.id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
def delete_asset(request):
    """Delete an asset.
    
    Removes:
    - Asset record
    - Associated barrier links
    - Risk assessments
    - Asset link associations
    
    This is a destructive operation that cannot be undone.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')
        asset = get_object_or_404(Asset, id=asset_id)
        asset.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_asset_form(request, asset_id=None):
    """Get the asset form for editing.
    
    Provides:
    - Asset details form
    - Available asset types
    - Country selection
    - Barrier selection
    - Scenario selection
    
    Args:
        asset_id (int, optional): ID of the asset to edit. If None, provides form for new asset.
    """
    asset = get_object_or_404(Asset, id=asset_id) if asset_id else None
    
    context = {
        'asset': asset,
        'asset_types': AssetType.objects.all(),
        'countries': Country.objects.filter(company_operated=True),
        'barriers': Barrier.objects.all(),
        'scenarios': Scenario.objects.all(),
    }
    return render(request, 'partials/asset_form.html', context)

@login_required
def get_asset_barriers(request, asset_id):
    """Get the barriers for a specific asset.
    
    Shows:
    - Assigned barriers
    - Barrier effectiveness scores
    - Barrier characteristics
    - Recent barrier assessments
    """
    asset = get_object_or_404(Asset, id=asset_id)
    barriers = asset.barriers.all().select_related('category').prefetch_related(
        'effectiveness_scores',
        'characteristic_assessments'
    )
    
    context = {
        'asset': asset,
        'barriers': barriers,
        'barrier_categories': BarrierCategory.objects.all(),
    }
    return render(request, 'partials/asset_barriers.html', context)

@login_required
def get_asset_barriers_list(request, asset_id):
    """Get a list of barriers for a specific asset.
    
    Returns a simple list of barrier IDs and names,
    used primarily for dropdown menus and quick selection.
    """
    asset = get_object_or_404(Asset, id=asset_id)
    barriers = asset.barriers.all().values('id', 'name')
    return JsonResponse({'barriers': list(barriers)})

@login_required
@csrf_exempt
def add_asset_barrier(request):
    """Add a barrier to an asset.
    
    Creates:
    - Asset-barrier association
    - Initial effectiveness scores
    - Default characteristic assessments
    
    This sets up the basic barrier configuration for the asset.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        asset_id = request.POST.get('asset_id')
        barrier_id = request.POST.get('barrier_id')
        
        asset = get_object_or_404(Asset, id=asset_id)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        # Check if barrier is already assigned
        if barrier in asset.barriers.all():
            return JsonResponse({
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
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@csrf_exempt
def remove_asset_barrier(request):
    """Remove a barrier from an asset.
    
    Removes:
    - Asset-barrier association
    - Related effectiveness scores
    - Assessment history
    
    Updates the asset's risk matrices to reflect the removal.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        asset_id = data.get('asset_id')
        barrier_id = data.get('barrier_id')
        
        asset = get_object_or_404(Asset, id=asset_id)
        barrier = get_object_or_404(Barrier, id=barrier_id)
        
        # Remove barrier from asset
        asset.barriers.remove(barrier)
        
        # Update risk matrices
        FinalRiskMatrix.generate_matrices(asset)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
