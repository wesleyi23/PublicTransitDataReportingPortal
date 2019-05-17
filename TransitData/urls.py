"""TransitData URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from Panacea import views


urlpatterns = [
    # path('test/', views.testView, name="testView"),
    path('', views.dashboard, name="dashboard"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('logout/', views.logout_view, name="logout"),
    path('ProfileSetup/', views.ProfileSetup, name="ProfileSetup"),
    path('ProfileSetup/Review/', views.ProfileSetup_Review, name="ProfileSetup_Review"),
    path('ProfileSetup/PhoneAndOrg/', views.ProfileSetup_PhoneAndOrg, name="ProfileSetup_PhoneAndOrg"),
    path('ProfileSetup/ReportSelection/', views.ProfileSetup_ReportSelection, name="ProfileSetup_ReportSelection"),
    path('AssetInvReport/Report/', views.Vanpool_report, name="Vanpool_report"),
    path('AssetInvReport/Report/<int:year>/<int:month>/', views.Vanpool_report, name="Vanpool_report"),
    path('AssetInvReport/Data/', views.Vanpool_data, name="Vanpool_data"),
    path('AssetInvReport/Other/', views.Vanpool_other, name="Vanpool_other"),
    path('UserProfile/', views.UserProfile, name="UserProfile"),
    path('OrganizationProfile/', views.OrganizationProfile, name="OrganizationProfile"),
    path('OrganizationProfile/Users', views.OrganizationProfileUsers, name = "OrganizationProfileUsers"),
    path('Permissions/', views.Permissions, name="Permissions"),
    path('Admin/Reports/', views.Admin_reports, name="Admin_reports"),
    path('Admin/Expansion/', views.Vanpool_expansion_analysis, name="Vanpool_expansion_analysis"),
    path('Admin/Vanpool_expansion_modify', views.Vanpool_expansion_modify, name = "Vanpool_expansion_modify"),
    path('Admin/Vanpool_expansion_modify/<int:id>', views.Vanpool_expansion_modify, name = "Vanpool_expansion_modify"),
    path('Admin/Vanpool_expansion_submission/', views.Vanpool_expansion_submission, name = "Vanpool_expansion_submission"),
    path('Admin/ReminderEmail/', views.Admin_ReminderEmail, name="Admin_ReminderEmail"),
    path('Admin/AssignPermissions/', views.Admin_assignPermissions, name="Admin_assignPermissions"),
    path('Help/', views.Help, name="Help"),
    path('Panacea/register/', views.register, name='register'),
    path('admin/', admin.site.urls),
    path('Panacea/', include('Panacea.urls')),
    path('Panacea/', include('django.contrib.auth.urls')),

]

handler404 = views.handler404