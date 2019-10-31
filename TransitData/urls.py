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
    path('vanpool/Report/', views.Vanpool_report, name="Vanpool_report"),
    path('vanpool/Report/<int:year>/<int:month>/', views.Vanpool_report, name="Vanpool_report"),
    path('vanpool/Data/', views.Vanpool_data, name="Vanpool_data"),
    path('vanpool/statewide_summary/', views.vanpool_statewide_summary, name="vanpool_statewide_summary"),
    path('vanpool/organization_summary/', views.vanpool_organization_summary, name="vanpool_organization_summary"),
    path('vanpool/organization_summary/<int:org_id>/', views.vanpool_organization_summary, name="vanpool_organization_summary"),
    path('UserProfile/', views.UserProfile, name="UserProfile"),
    path('OrganizationProfile/', views.OrganizationProfile, name="OrganizationProfile"),
    path('OrganizationProfile/<redirect_to>/', views.OrganizationProfile, name="OrganizationProfile"),
    path('OrganizationProfile/Users', views.OrganizationProfileUsers, name="OrganizationProfileUsers"),
    path('Permissions/', views.Permissions, name="Permissions"),
    path('Admin/Expansion/', views.Vanpool_expansion_analysis, name="Vanpool_expansion_analysis"),
    path('Admin/Operation_Summary', views.Operation_Summary, name='Operation_Summary'),
    path('Admin/VanpoolGrowth', views.Vanpool_Growth, name='Vanpool_Growth'),
    path('Admin/Vanpool_expansion_modify', views.Vanpool_expansion_modify, name="Vanpool_expansion_modify"),
    path('Admin/Vanpool_expansion_modify/<int:id>', views.Vanpool_expansion_modify, name="Vanpool_expansion_modify"),
    path('Admin/Vanpool_expansion_submission/', views.Vanpool_expansion_submission, name="Vanpool_expansion_submission"),
    path('Admin/AssignPermissions/<active>', views.Admin_assignPermissions, name="Admin_assignPermissions"),
    path('Help/', views.help_page, name="Help"),
    path('Panacea/register/', views.register, name='register'),
    path('admin/', admin.site.urls),
    path('Panacea/', include('Panacea.urls')),
    path('Panacea/', include('django.contrib.auth.urls')),
    path('accessibility', views.accessibility, name='accessibility'),
    path('PublicDisclosure/', views.public_disclosure, name="public_disclosure"),
    path('summary/instructions/', views.summary_instructions, name="summary_instructions"),
    path('summary/organizational_information/', views.organizational_information, name="organizational_information"),
    path('summary/ntd_upload/', views.ntd_upload, name="ntd_upload"),
    path('summary/cover_sheets/organization', views.cover_sheet_organization_view, name="cover_sheets_organization"),
    path('summary/cover_sheets/service', views.cover_sheet_service_view, name="cover_sheets_service"),
    path('summary/report_data/', views.summary_report_data, name = 'summary_report_data'),
    path('summary/report_data/confirm_mode', views.summary_modes, name = 'summary_modes'),
    path('summary/report_data/report_transit_data', views.report_transit_data, name = 'report_transit_data'),
    path('summary/report_data/report_revenue', views.report_revenues, name = 'report_revenues'),
    path('summary/report_data/report_expenses/', views.report_expenses, name='report_expenses'),
    path('summary/report_data/report_expenses/<int:year>', views.report_expenses, name='report_expenses'),
    path('summary/report_data/review_data', views.review_data, name='review_data'),
    path('summary/test', views.test, name='test'),

]

handler404 = views.handler404