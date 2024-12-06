"""
Core application views.
This package contains all the views for the GEMS application, organized by functionality:

- dashboard_views: Dashboard data API endpoints
- country_views: Country management and BTA handling API endpoints
- asset_views: Asset management API endpoints
- risk_views: Risk assessment API endpoints
- barrier_views: Barrier management API endpoints
- analysis_views: Analysis and recommendations API endpoints
"""

from .dashboard_views import (
    get_dashboard_data,
    get_security_manager_data,
)

from .country_views import (
    search_countries,
    add_operated_country,
    remove_operated_country,
    get_country_geojson,
    get_operated_countries_geojson,
    save_country_details,
    save_bta,
)

from .asset_views import (
    get_global_assets,
    get_asset_details,
    get_asset_risk_data,
    save_asset,
    delete_asset,
    get_asset_form_data,
    get_asset_barriers,
    get_asset_barriers_list,
    add_asset_barrier,
    remove_asset_barrier,
    manage_asset_links,
    update_linked_assets,
)

from .risk_views import (
    get_risk_assessment_data,
    save_risk_assessment,
    get_risk_matrix_data,
    generate_risk_matrix,
    save_step_data,
)

from .analysis_views import (
    get_trend_analysis,
    get_recommendations,
)

from .barrier_views import (
    get_barrier_assessments,
    get_barrier_details,
    save_barrier_scenarios,
    save_barrier_effectiveness,
    get_barrier_trends,
    report_barrier_issue,
    resolve_barrier_issue,
    get_barriers_by_category,
)

# For convenience, expose all views at the package level
__all__ = [
    # Dashboard views
    'get_dashboard_data',
    'get_security_manager_data',
    
    # Country views
    'search_countries',
    'add_operated_country',
    'remove_operated_country',
    'get_country_geojson',
    'get_operated_countries_geojson',
    'save_country_details',
    'save_bta',
    
    # Asset views
    'get_global_assets',
    'get_asset_details',
    'get_asset_risk_data',
    'save_asset',
    'delete_asset',
    'get_asset_form_data',
    'get_asset_barriers',
    'get_asset_barriers_list',
    'add_asset_barrier',
    'remove_asset_barrier',
    'manage_asset_links',
    'update_linked_assets',
    
    # Risk views
    'get_risk_assessment_data',
    'save_risk_assessment',
    'get_risk_matrix_data',
    'generate_risk_matrix',
    'save_step_data',
    
    # Analysis views
    'get_trend_analysis',
    'get_recommendations',
    
    # Barrier views
    'get_barrier_assessments',
    'get_barrier_details',
    'save_barrier_scenarios',
    'save_barrier_effectiveness',
    'get_barrier_trends',
    'report_barrier_issue',
    'resolve_barrier_issue',
    'get_barriers_by_category',
]
