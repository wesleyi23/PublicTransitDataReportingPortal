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
    path('test_tools/', views.test_tools, name="test_tools"),
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
    path('summary/pick_up_where_you_left_off', views.pick_up_where_you_left_off, name="pick_up_where_you_left_off"),
    path('summary/cover_sheet_submitted/', views.cover_sheet_submitted, name="cover_sheet_submitted"),
    path('summary/organizational_information/', views.organizational_information, name="organizational_information"),
    path('summary/submit_cover_sheet/', views.submit_cover_sheet, name="submit_cover_sheet"),
    path('summary/submit_cover_sheet/submit', views.submit_cover_sheet_submit, name="submit_cover_sheet_submit"),
    path('summary/ntd_upload/', views.ntd_upload, name="ntd_upload"),
    path('summary/cover_sheets/organization', views.cover_sheet_organization_view, name="cover_sheets_organization"),
    path('summary/cover_sheets/service', views.cover_sheet_service_view, name="cover_sheets_service"),
    path('summary/report_data/instructions', views.summary_report_data, name='summary_report_data'),
    path('summary/report_data/confirm_mode', views.summary_modes, name='summary_modes'),
    path('summary/report_data/data_reported', views.data_submitted, name="data_submitted"),
    path('summary/report_data/confirm_service', views.summary_modes, name='summary_modes'),
    path('summary/report_data/accept_service', views.accept_modes, name='accept_modes'),
    path('summary/report_data/delete_mode/<name>/<admin_of_mode>', views.delete_summary_mode, name='delete_summary_mode'),
    path('summary/report_data/delete_mode/', views.delete_summary_mode, name='delete_summary_mode_root'),
    path('summary/report_data/review_data', views.review_data, name='review_data'),
    path('summary/report_data/', views.summary_reporting, name='summary_reporting'),
    path('summary/report_data/<report_type>', views.summary_reporting, name='summary_reporting_type'),
    path('summary/report_data/<report_type>/<form_filter_1>/<form_filter_2>', views.summary_reporting, name='summary_reporting_filters'),
    path('summary/submit_data', views.submit_data, name="submit_data"),
    path('summary/submit_data/submit', views.submit_data_submit, name="submit_data_submit"),
    path('summary/admin/configure_agency_types/', views.configure_agency_types, name='summary_configure_agency_types'),
    path('summary/admin/configure_agency_types/<model>', views.configure_agency_types, name='summary_configure_agency_types'),
    path('summary/view_agency_report', views.view_annual_operating_information, name = 'view_transit_data'),
    path('summary/view_financial_data', views.view_financial_information, name = 'view_financial_data'),
    path('summary/view_agency_rollup', views.view_rollup, name = 'view_rollup_data'),
    path('summary/view_performance_measures', views.view_performance_measures, name = 'view_performance_measures'),
    path('summary/view_statewide_measures', views.view_statewide_measures, name = 'view_statewide_measures'),
    path('summary/view_statewide_rollup', views.view_statewide_rollup, name = 'view_statewide_rollup'),
    path('summary/view_statewide_statistics', views.view_statewide_statistics, name = 'view_statewide_statistics'),
    path('summary/admin/tracking/new/<int:year>', views.create_new_tracking_year, name="create_new_tracking_year"),
    path('summary/admin/summary_tracking', views.summary_tracking, name="summary_tracking"),
    path('summary/admin/summary_tracking/<int:year>', views.summary_tracking, name="summary_tracking_year"),
    path('summary/admin/yearly_setup_instructions>', views.summary_yearly_setup_instructions, name="yearly_setup_instructions"),
    path('summary/admin/yearly_setup', views.summary_yearly_setup, name="yearly_setup"),
    path('summary/admin/metric_configurations', views.summary_metric_configurations, name="metric_configurations"),
    path('summary/admin/metric_configurations/<report_type>', views.summary_metric_configurations, name="metric_configurations"),
    path('summary/admin/yearly_setup/<action>', views.summary_yearly_setup, name="yearly_setup_action"),
    path('summary/admin/wsdot_review_cover_sheet', views.wsdot_review_cover_sheets, name="wsdot_review_cover_sheets"),
    path('summary/admin/wsdot_review_cover_sheet/<int:year>', views.wsdot_review_cover_sheets, name="wsdot_review_cover_sheets_year"),
    path('summary/admin/wsdot_review_cover_sheet/<int:year>/<int:organization_id>', views.wsdot_review_cover_sheets, name="wsdot_review_cover_sheets_year_org"),
    path('summary/admin/wsdot_review_cover_sheet/add_note_wsdot_child/<int:parent_note>/', views.add_cover_sheet_child_note_wsdot, name="add_cover_sheet_note_wsdot_child"),
    path('summary/admin/wsdot_review_cover_sheet/add_note/<int:year>/<summary_report_status_id>', views.base_note, name="base_wsdot_note_url"),
    path('summary/admin/wsdot_review_cover_sheet/add_note_wsdot_child', views.base_note, name="base_wsdot_note_child_url"),
    path('summary/admin/review_cover_sheets/add_note', views.add_cover_sheet_child_note_customer, name="base_add_cover_sheet_child_note_customer"),
    path('summary/admin/wsdot_review_cover_sheet/add_note/<int:year>/<int:summary_report_status_id>/<note_area>/<note_field>/', views.add_cover_sheet_note_wsdot, name="add_cover_sheet_note_wsdot_parent"),
    path('summary/admin/wsdot_review_cover_sheet/add_note_customer/<int:year>/<note_area>/<note_field>/', views.add_cover_sheet_note_customer, name="add_cover_sheet_note_customer_parent"),
    path('summary/admin/wsdot_review_cover_sheet/delete_note/<int:note_id>', views.delete_cover_sheet_note, name="delete_cover_sheet_note"),
    path('summary/admin/wsdot_review_cover_sheet/approve_cover_sheet/<int:summary_report_status_id>', views.approve_cover_sheet, name="approve_cover_sheet"),
    path('summary/admin/wsdot_review_cover_sheet/return_cover_sheet_to_user/<int:summary_report_status_id>', views.return_cover_sheet_to_user, name="return_cover_sheet_to_user"),
    path('summary/admin/review_cover_sheets', views.wsdot_review_data, name="wsdot_review_data"),
    path('summary/admin/review_cover_sheets/add_note/<int:parent_note>/', views.add_cover_sheet_child_note_customer, name="add_cover_sheet_child_note_customer"),
    path('summary/review_organization_information', views.customer_review_cover_sheets, name="customer_review_cover_sheets"),
    path('summary/customer_review_data', views.customer_review_data, name="customer_review_data"),
    path('summary/customer_review_instructions', views.customer_review_instructions, name="customer_review_instructions"),
    path('summary/customer_review/accept_edit/accept_wsdot_edit/<int:note_id>', views.accept_wsdot_edit, name="accept_wsdot_edit"),
    path('logged_in/', views.your_logged_in, name='your_logged_in'),
    path('login_denied/', views.login_denied, name='login_denied'),
    path('sso/wsdot/', views_SAML.signin, name="wsdot_sso"),
    path('sso/wsdot/reply/', views_SAML.wsdot, name="wsdot_sso_reply"),
    # path('summary/test', views.test, name='test'),

]

handler404 = views.handler404