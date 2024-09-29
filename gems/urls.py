from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('countries/', views.countries_list_view, name='countries_list_view'),
    path('country/<int:country_id>/', views.country_detail_view, name='country_detail_view'),
    path('asset/<int:asset_id>/', views.asset_detail_view, name='asset_detail_view'),
    path('global-assets/', views.global_assets_view, name='global_assets_view'),
    path('security_manager/dashboard/', views.security_manager_dashboard, name='security_manager_dashboard'),
    path('security_manager/save_country/', views.save_country_details, name='save_country_details'),
    path('security_manager/save_asset/', views.save_asset, name='save_asset'),
    path('security_manager/delete_asset/', views.delete_asset, name='delete_asset'),
    path('security_manager/save_bta/', views.save_bta, name='save_bta'),
]
