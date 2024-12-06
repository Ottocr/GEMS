from django.contrib import admin
from django.urls import path
from rest_framework.authtoken import views as auth_views
from core.views import (
    country_views,
    asset_views,
    risk_views,
    dashboard_views,
    analysis_views,
    barrier_views,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication
    path('api/token-auth/', auth_views.obtain_auth_token, name='api_token_auth'),
    
    # Dashboard API Endpoints
    path('api/dashboard/data/', dashboard_views.get_dashboard_data, name='dashboard_data'),
    path('api/security-manager/data/', dashboard_views.get_security_manager_data, name='security_manager_data'),
    
    # Country API Endpoints
    path('api/countries/search/', country_views.search_countries, name='search_countries'),
    path('api/countries/operated/add/', country_views.add_operated_country, name='add_operated_country'),
    path('api/countries/operated/remove/', country_views.remove_operated_country, name='remove_operated_country'),
    path('api/countries/<int:country_id>/geojson/', country_views.get_country_geojson, name='get_country_geojson'),
    path('api/countries/operated/geojson/', country_views.get_operated_countries_geojson, name='get_operated_countries_geojson'),
    path('api/countries/save/', country_views.save_country_details, name='save_country_details'),
    path('api/countries/bta/save/', country_views.save_bta, name='save_bta'),
    
    # Asset API Endpoints
    path('api/assets/', asset_views.get_global_assets, name='get_global_assets'),
    path('api/assets/<int:asset_id>/', asset_views.get_asset_details, name='get_asset_details'),
    path('api/assets/<int:asset_id>/risk-data/', asset_views.get_asset_risk_data, name='get_asset_risk_data'),
    path('api/assets/save/', asset_views.save_asset, name='save_asset'),
    path('api/assets/delete/', asset_views.delete_asset, name='delete_asset'),
    path('api/assets/form-data/', asset_views.get_asset_form_data, name='get_asset_form_data'),
    path('api/assets/form-data/<int:asset_id>/', asset_views.get_asset_form_data, name='get_asset_form_data_edit'),
    path('api/assets/<int:asset_id>/barriers/', asset_views.get_asset_barriers, name='get_asset_barriers'),
    path('api/assets/<int:asset_id>/barriers/list/', asset_views.get_asset_barriers_list, name='get_asset_barriers_list'),
    path('api/assets/barriers/add/', asset_views.add_asset_barrier, name='add_asset_barrier'),
    path('api/assets/barriers/remove/', asset_views.remove_asset_barrier, name='remove_asset_barrier'),
    path('api/assets/links/', asset_views.manage_asset_links, name='manage_asset_links'),
    path('api/assets/links/<int:asset_link_id>/update/', asset_views.update_linked_assets, name='update_linked_assets'),
    
    # Risk Assessment API Endpoints
    path('api/risk-assessment/data/', risk_views.get_risk_assessment_data, name='get_risk_assessment_data'),
    path('api/risk-assessment/save/', risk_views.save_risk_assessment, name='save_risk_assessment'),
    path('api/risk-matrix/data/', risk_views.get_risk_matrix_data, name='get_risk_matrix_data'),
    path('api/risk-matrix/generate/', risk_views.generate_risk_matrix, name='generate_risk_matrix'),
    path('api/risk-matrix/step/save/', risk_views.save_step_data, name='save_step_data'),
    
    # Analysis API Endpoints
    path('api/analysis/trends/', analysis_views.get_trend_analysis, name='get_trend_analysis'),
    path('api/analysis/recommendations/<int:asset_id>/', analysis_views.get_recommendations, name='get_recommendations'),
    
    # Barrier API Endpoints
    path('api/barriers/', barrier_views.get_barrier_assessments, name='get_barrier_assessments'),
    path('api/barriers/<int:barrier_id>/', barrier_views.get_barrier_details, name='get_barrier_details'),
    path('api/barriers/<int:barrier_id>/scenarios/save/', barrier_views.save_barrier_scenarios, name='save_barrier_scenarios'),
    path('api/barriers/<int:barrier_id>/effectiveness/save/', barrier_views.save_barrier_effectiveness, name='save_barrier_effectiveness'),
    path('api/barriers/<int:barrier_id>/trends/', barrier_views.get_barrier_trends, name='get_barrier_trends'),
    path('api/barriers/issues/report/', barrier_views.report_barrier_issue, name='report_barrier_issue'),
    path('api/barriers/issues/<int:issue_id>/resolve/', barrier_views.resolve_barrier_issue, name='resolve_barrier_issue'),
    path('api/barriers/category/<int:category_id>/', barrier_views.get_barriers_by_category, name='get_barriers_by_category'),
    path('admin/core/risksubtype/', barrier_views.get_risk_subtypes, name='admin_get_risk_subtypes'),  # New endpoint for admin interface
]
