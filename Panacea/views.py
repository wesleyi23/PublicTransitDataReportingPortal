import json

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.urls import reverse_lazy
from django.utils.datetime_safe import datetime
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.generic import TemplateView

from .forms import CustomUserCreationForm, custom_user_ChangeForm, PhoneOrgSetup, ReportSelection, VanpoolMonthlyReport
from django.utils.translation import ugettext_lazy as _
from .models import profile, vanpool_report



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required(login_url='Panacea/login')
def index(request):
    return render(request, 'index.html', {})


@login_required(login_url='Panacea/login')
def dashboard(request):
    myProfile = profile.objects.get(custom_user=request.user)

    if myProfile.profile_complete is True:
        return render(request, 'pages/dashboard.html')
    elif myProfile.profile_submitted is True:
        return render(request, 'pages/ProfileComplete.html')
    else:
        return redirect('ProfileSetup')


@login_required(login_url='Panacea/login')
def ProfileSetup(request):
    form1 = custom_user_ChangeForm(instance=request.user)
    myInstance = profile.objects.get(custom_user=request.user.id)
    form2 = PhoneOrgSetup(instance=myInstance)
    form3 = ReportSelection(instance=myInstance)
    return render(request, 'pages/ProfileSetup.html', {'ProfileSetup_PhoneAndOrg': form2,
                                                       'custom_user_ChangeForm': form1,
                                                       'ProfileSetup_ReportSelection': form3})


@login_required(login_url='Panacea/login')
def ProfileSetup_Review(request):
    if request.method == 'POST':
        user = request.user
        if request.POST:
            form = custom_user_ChangeForm(request.POST, instance=user)
            if form.is_valid():
                form.user = request.user
                form = form.save(commit=False)
                form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': form.errors})


@login_required(login_url='Panacea/login')
def ProfileSetup_PhoneAndOrg(request):
    if request.method == 'POST':
        myInstance = profile.objects.get(custom_user=request.user.id)
        if request.POST:
            form = PhoneOrgSetup(request.POST, instance=myInstance)
            if form.is_valid():
                form.user = request.user
                form = form.save(commit=False)
                form.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'error': form.errors}, status=200)

@login_required(login_url='Panacea/login')
def ProfileSetup_ReportSelection(request):
    if request.method == 'POST':
        myInstance = profile.objects.get(custom_user=request.user.id)
        if request.POST:
            form = ReportSelection(request.POST, instance=myInstance)
            if form.is_valid():
                # form.user = request.user
                form.save()
                myInstance.profile_submitted = True
                myInstance.save()
                return JsonResponse({'redirect': '../dashboard'})
            else:
                return JsonResponse({'error': form.errors})


@login_required(login_url='Panacea/login')
def Vanpool_report(request, year=None, month=None):
    if not year:
        year = 2019
    if not month:
        month = 1

    user_organization = profile.objects.get(custom_user=request.user.id).organization

    past_report_data = vanpool_report.objects.filter(organization_id=user_organization, report_year=year)
    form_data = vanpool_report.objects.get(organization_id=user_organization.id, report_year=year, report_month=month)

    if request.method == 'POST':
        form = VanpoolMonthlyReport(request.POST, instance=form_data)
        if form.is_valid():
            form.save()
            successful_submit = True
            return render(request, 'pages/Vanpool_report.html', {'form': form,
                                                                 'past_report_data': past_report_data,
                                                                 'year': year,
                                                                 'month': month,
                                                                 'organization': user_organization,
                                                                 'successful_submit': successful_submit}
                          )
        else:
            successful_submit = False
            # form = VanpoolMonthlyReport(instance=form_data)
            return render(request, 'pages/Vanpool_report.html', {'form': form,
                                                                 'past_report_data': past_report_data,
                                                                 'year': year,
                                                                 'month': month,
                                                                 'organization': user_organization,
                                                                 'successful_submit': successful_submit}
                          )
    else:
        form = VanpoolMonthlyReport(instance=form_data)
        successful_submit = False
        return render(request, 'pages/Vanpool_report.html', {'form': form,
                                                             'past_report_data': past_report_data,
                                                             'year': year,
                                                             'month': month,
                                                             'organization': user_organization,
                                                             'successful_submit': successful_submit}
                      )




@login_required(login_url='Panacea/login')
def Vanpool_data(request):
    return render(request, 'pages/Vanpool_data.html', {})


@login_required(login_url='Panacea/login')
def Vanpool_other(request):
    return render(request, 'pages/Vanpool_other.html', {})


@login_required(login_url='Panacea/login')
def UserProfile(request):
    return render(request, 'pages/UserProfile.html', {})


@login_required(login_url='Panacea/login')
def OrganizationProfile(request):
    return render(request, 'pages/OrganizationProfile.html', {})


@login_required(login_url='Panacea/login')
def Permissions(request):
    return render(request, 'pages/Permissions.html', {})


@login_required(login_url='Panacea/login')
def Admin_reports(request):
    return render(request, 'pages/AdminReports.html', {})


@login_required(login_url='Panacea/login')
def Admin_ReminderEmail(request):
    return render(request, 'pages/ReminderEmail.html', {})


@login_required(login_url='Panacea/login')
def Admin_assignPermissions(request):
    return render(request, 'pages/AssignPermissions.html', {})

@login_required(login_url='Panacea/login')
def Help(request):
    return render(request, 'pages/Help.html', {})

