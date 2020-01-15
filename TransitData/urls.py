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
from Panacea import views_SAML
from django.conf.urls import url

urlpatterns = [
    # # These are the SAML2 related URLs. You can change "^saml2_auth/" regex to
    # # any path you want, like "^sso_auth/", "^sso_login/", etc. (required)
    # url('sso/', include('django_saml2_auth.urls')),
    #
    # # The following line will replace the default user login with SAML2 (optional)
    # # If you want to specific the after-login-redirect-URL, use parameter "?next=/the/path/you/want"
    # # with this view.
    # url(r'^accounts/login/$', django_saml2_auth.views.signin),
    #
    # # The following line will replace the admin login with SAML2 (optional)
    # # If you want to specific the after-login-redirect-URL, use parameter "?next=/the/path/you/want"
    # # with this view.
    # url(r'^admin/login/$', django_saml2_auth.views.signin),
    # # path('test/', views.testView, name="testView"),
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
    path('vanpool/download_vanpool_data', views.download_vanpool_data, name = 'download_vanpool_data'),
    path('vanpool/statewide_summary/', views.vanpool_statewide_summary, name="vanpool_statewide_summary"),
    path('vanpool/organization_summary/', views.vanpool_organization_summary, name="vanpool_organization_summary"),
    path('vanpool/organization_summary/<int:org_id>/', views.vanpool_organization_summary, name="vanpool_organization_summary"),
    path('ContactUs/', views.contact_us, name = 'ContactUs'),
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
    path('accessibility/', views.accessibility, name='accessibility'),
    path('PublicDisclosure/', views.public_disclosure, name="public_disclosure"),
    path('summary/instructions/', views.summary_instructions, name="summary_instructions"),
    path('summary/organizational_information/', views.organizational_information, name="organizational_information"),
    path('summary/ntd_upload/', views.ntd_upload, name="ntd_upload"),
    path('summary/cover_sheets/organization', views.cover_sheet_organization_view, name="cover_sheets_organization"),
    path('summary/cover_sheets/service', views.cover_sheet_service_view, name="cover_sheets_service"),
    path('summary/report_data/instructions', views.summary_report_data, name='summary_report_data'),
    path('summary/report_data/confirm_mode', views.summary_modes, name='summary_modes'),
    path('summary/report_data/delete_mode/<name>/<admin_of_mode>', views.delete_summary_mode, name='delete_summary_mode'),
    path('summary/report_data/delete_mode/', views.delete_summary_mode, name='delete_summary_mode_root'),
    path('summary/report_data/review_data', views.review_data, name='review_data'),
    path('summary/report_data/', views.summary_reporting, name='summary_reporting'),
    path('summary/report_data/<report_type>', views.summary_reporting, name='summary_reporting_type'),
    path('summary/report_data/<report_type>/<form_filter_1>/<form_filter_2>', views.summary_reporting, name='summary_reporting_filters'),
    path('summary/admin/configure_agency_types/', views.configure_agency_types, name='summary_configure_agency_types'),
    path('summary/admin/configure_agency_types/<model>', views.configure_agency_types, name='summary_configure_agency_types'),
    path('summary/view_agency_report', views.view_agency_report, name = 'view_agency_report'),
    path('summary/admin/review_cover_sheets', views.review_cover_sheets, name="review_cover_sheets"),
    path('logged_in/', views.your_logged_in, name='your_logged_in'),
    path('login_denied/', views.login_denied, name='login_denied'),
    path('sso/wsdot/', views_SAML.signin, name="wsdot_sso"),
    path('sso/wsdot/reply/', views_SAML.wsdot, name="wsdot_sso_reply"),
    # path('summary/test', views.test, name='test'),

]

handler404 = views.handler404