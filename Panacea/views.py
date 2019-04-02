from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic

from .forms import CustomUserCreationForm


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('index')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required(login_url='Panacea/login')
def index(request):
    return render(request, 'index.html', {})


@login_required(login_url='Panacea/login')
def dashboard(request):
    return render(request, 'pages/dashboard.html', {})


@login_required(login_url='Panacea/login')
def AssetInvReport_report(request):
    return render(request, 'pages/AssetInvReport_report.html', {})


@login_required(login_url='Panacea/login')
def AssetInvReport_data(request):
    return render(request, 'pages/AssetInvReport_data.html', {})


@login_required(login_url='Panacea/login')
def AssetInvReport_other(request):
    return render(request, 'pages/AssetInvReport_other.html', {})


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