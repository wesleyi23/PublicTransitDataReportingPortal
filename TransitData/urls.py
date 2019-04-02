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
    path('', views.dashboard, name="dashboard"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('AssetInvReport/Report/', views.AssetInvReport_report, name="AssetInvReport_report"),
    path('AssetInvReport/Data/', views.AssetInvReport_data, name="AssetInvReport_data"),
    path('AssetInvReport/Other/', views.AssetInvReport_other, name="AssetInvReport_other"),
    path('UserProfile/', views.UserProfile, name="UserProfile"),
    path('OrganizationProfile/', views.OrganizationProfile, name="OrganizationProfile"),
    path('Permissions/', views.Permissions, name="Permissions"),
    path('Admin/Reports/', views.Admin_reports, name="Admin_reports"),
    path('Admin/ReminderEmail/', views.Admin_ReminderEmail, name="Admin_ReminderEmail"),
    path('Admin/AssignPermissions/', views.Admin_assignPermissions, name="Admin_assignPermissions"),
    path('Help/', views.Help, name="Help"),
    path('Panacea/register/', views.register, name='register'),
    path('admin/', admin.site.urls),
    path('Panacea/', include('Panacea.urls')),
    path('Panacea/', include('django.contrib.auth.urls')),

]
