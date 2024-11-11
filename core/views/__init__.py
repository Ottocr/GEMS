"""
Core application views.
This package contains all the views for the GEMS application, organized by functionality:

- dashboard_views: Main dashboard and security manager dashboard views
- country_views: Country management and BTA handling
- asset_views: Asset management, linking, and barrier associations
- risk_views: Risk assessment workflow and matrix generation
- barrier_views: Barrier assessments, trends, and issue reporting
- analysis_views: Trend analysis and recommendations
"""

from .dashboard_views import (
    dashboard,
    security_manager_dashboard,
)

from .country_views import (
    countries_list_view,
    country_detail_view,
    save_country_details,
    save_bta,
)

from .asset_views import (
    save_asset,
    delete_asset,
    get_asset_form,
    get_asset_barriers,
    get_asset_barriers_list,
    add_asset_barrier,
    remove_asset_barrier,
)

from .risk_views import (
    risk_assessment_workflow,
    save_risk_assessment,
    risk_matrix_generator,
    generate_risk_matrix,
    save_step_data,
)

# For convenience, expose all views at the package level
__all__ = [
    # Dashboard views
    'dashboard',
    'security_manager_dashboard',
    
    # Country views
    'countries_list_view',
    'country_detail_view',
    'save_country_details',
    'save_bta',
    
    # Asset views
    'save_asset',
    'delete_asset',
    'get_asset_form',
    'get_asset_barriers',
    'get_asset_barriers_list',
    'add_asset_barrier',
    'remove_asset_barrier',
    
    # Risk views
    'risk_assessment_workflow',
    'save_risk_assessment',
    'risk_matrix_generator',
    'generate_risk_matrix',
    'save_step_data',
]
