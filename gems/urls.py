from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core.views import (
    dashboard_views,
    country_views,
    asset_views,
    risk_views,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', dashboard_views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboards
    path('dashboard/', dashboard_views.dashboard, name='dashboard'),
    path('security-manager/', dashboard_views.security_manager_dashboard, name='security_manager_dashboard'),
    
    # Security Manager Functionality
    path('security_manager/save_country/', country_views.save_country_details, name='save_country_details'),
    path('security_manager/save_bta/', country_views.save_bta, name='save_bta'),
    
    # Asset Management (needed for security manager dashboard)
    path('security_manager/save_asset/', asset_views.save_asset, name='save_asset'),
    path('security_manager/delete_asset/', asset_views.delete_asset, name='delete_asset'),
    path('security_manager/get_asset_form/', asset_views.get_asset_form, name='get_asset_form'),
    path('security_manager/get_asset_form/<int:asset_id>/', asset_views.get_asset_form, name='get_asset_form_edit'),
    path('security_manager/get_asset_barriers/<int:asset_id>/', asset_views.get_asset_barriers, name='get_asset_barriers'),
    path('security_manager/get_asset_barriers/<int:asset_id>/list/', asset_views.get_asset_barriers_list, name='get_asset_barriers_list'),
    path('asset/barrier/add/', asset_views.add_asset_barrier, name='add_asset_barrier'),
    path('asset/barrier/remove/', asset_views.remove_asset_barrier, name='remove_asset_barrier'),
    
    # Risk Assessment & Matrix
    path('risk-assessment/', risk_views.risk_assessment_workflow, name='risk_assessment_workflow'),
    path('risk-assessment/save/', risk_views.save_risk_assessment, name='save_risk_assessment'),
    path('risk-matrix/', risk_views.risk_matrix_generator, name='risk_matrix_generator'),
    path('risk-matrix/generate/', risk_views.generate_risk_matrix, name='generate_risk_matrix'),
    path('risk-matrix/save-step/', risk_views.save_step_data, name='save_step_data'),
]
