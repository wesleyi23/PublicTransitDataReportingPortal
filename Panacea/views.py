import decimal
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Value
from django.forms import modelformset_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.db.models.functions import Concat
from django.template import RequestContext
from django.urls import reverse_lazy
from django.db.models.functions import datetime
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.generic import TemplateView
from django.forms.models import inlineformset_factory

from .forms import CustomUserCreationForm, \
    custom_user_ChangeForm, \
    PhoneOrgSetup, \
    ReportSelection, \
    VanpoolMonthlyReport, \
    user_profile_custom_user, \
    user_profile_profile, \
    organization_profile, \
    change_user_permissions_group, \
    chart_form
from django.utils.translation import ugettext_lazy as _
from .models import profile, vanpool_report, custom_user, organization


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


@login_required(login_url='/Panacea/login')
def index(request):
    return render(request, 'index.html', {})


@login_required(login_url='/Panacea/login')
def dashboard(request):
    myProfile = profile.objects.get(custom_user=request.user)

    if myProfile.profile_complete is True:
        return render(request, 'pages/dashboard.html')
    elif myProfile.profile_submitted is True:
        return render(request, 'pages/ProfileComplete.html')
    else:
        return redirect('ProfileSetup')


@login_required(login_url='/Panacea/login')
def ProfileSetup(request):
    form1 = custom_user_ChangeForm(instance=request.user)
    myInstance = profile.objects.get(custom_user=request.user.id)
    form2 = PhoneOrgSetup(instance=myInstance)
    form3 = ReportSelection(instance=myInstance)
    return render(request, 'pages/ProfileSetup.html', {'ProfileSetup_PhoneAndOrg': form2,
                                                       'custom_user_ChangeForm': form1,
                                                       'ProfileSetup_ReportSelection': form3})


@login_required(login_url='/Panacea/login')
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


@login_required(login_url='/Panacea/login')
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


@login_required(login_url='/Panacea/login')
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


@login_required(login_url='/Panacea/login')
def Vanpool_report(request, year=None, month=None):
    user_organization = profile.objects.get(custom_user=request.user.id).organization
    organization_data = vanpool_report.objects.filter(organization_id=user_organization)

    if not year:
        organization_data_incomplete = organization_data.filter(report_date=None)
        start_year = organization_data_incomplete \
            .aggregate(Min('report_year')) \
            .get('report_year__min')
        start_month = organization_data_incomplete.filter(report_year=start_year) \
            .aggregate(Min('report_month')) \
            .get('report_month__min')
        year = start_year
        month = start_month
    elif not month:
        month = 1

    min_year = organization_data.all().aggregate(Min('report_year')).get('report_year__min') == year
    max_year = organization_data.all().aggregate(Max('report_year')).get('report_year__max') == year

    past_report_data = vanpool_report.objects.filter(organization_id=user_organization, report_year=year)
    form_data = vanpool_report.objects.get(organization_id=user_organization.id, report_year=year, report_month=month)
    if form_data.report_date is None:
        new_report = True
    else:
        new_report = False

    if request.method == 'POST':
        form = VanpoolMonthlyReport(data=request.POST, instance=form_data)
        if form.is_valid():
            form.save()
            successful_submit = True
            new_report = False
        else:
            successful_submit = False

    else:
        form = VanpoolMonthlyReport(instance=form_data)
        successful_submit = False

    if not new_report:
        form.fields['data_change_explanation'].required = True



    return render(request, 'pages/Vanpool_report.html', {'form': form,
                                                         'past_report_data': past_report_data,
                                                         'year': year,
                                                         'month': month,
                                                         'organization': user_organization,
                                                         'successful_submit': successful_submit,
                                                         'min_year': min_year,
                                                         'max_year': max_year,
                                                         'new_report': new_report}
                  )


@login_required(login_url='/Panacea/login')
def Vanpool_data(request):

    def monthdelta(date, delta):
        delta = -int(delta)
        m, y = (date.month + delta) % 12, date.year + ((date.month) + delta - 1) // 12
        if not m: m = 12
        d = min(date.day, [31,
                           29 if y % 4 == 0 and not y % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][
            m - 1])
        return date.replace(day=d, month=m, year=y)

    def get_color(i):
        wsdot_colors = ["#2C8470",
                        "#97d700",
                        "#00aec7",
                        "#5F615E",
                        "#00b140",
                        "#007fa3",
                        "#ABC785",
                        "#593160"]
        j = i % 8
        return wsdot_colors[j]


    if request.POST:
        form = chart_form(data=request.POST)
        if form.is_valid:
            chart_title = form.MEASURE_CHOICES_DICT[form.data['chart_measure']]
            org_list = request.POST.getlist("chart_organizations")
            chart_time_frame = monthdelta(datetime.datetime.now().date(), form.data['chart_time_frame'])
            all_chart_data = [report for report in vanpool_report.objects.filter(organization_id__in=org_list).order_by('organization', 'report_year', 'report_month').all() if
                              chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
            chart_label = [report.report_year_month_label for report
                           in all_chart_data]
            chart_label = list(dict.fromkeys(chart_label))

            chart_datasets_filtered = {}

            i = 0
            for org in org_list:
                chart_dataset = [report for report in vanpool_report.objects.filter(organization_id=org).order_by('organization', 'report_year', 'report_month').all() if
                                 chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
                chart_dataset = [getattr(report, form.data['chart_measure']) for report in chart_dataset]
                chart_datasets_filtered[organization.objects.get(id=org).name] = [json.dumps(list(chart_dataset)), get_color(i)]
                i = i + 1

            return render(request, 'pages/Vanpool_data.html', {'form': form,
                                                               'chart_title': chart_title,
                                                               'chart_measure': form.data['chart_measure'],
                                                               'chart_label': chart_label,
                                                               'chart_datasets_filtered': chart_datasets_filtered,
                                                               'org_list': org_list
                                                               })

    else:
        defualt_chart_time_frame = 36
        user_organization_id = profile.objects.get(id=request.user.id).organization_id
        user_organization = organization.objects.get(id=user_organization_id)

        form = chart_form(initial={'chart_organizations': user_organization,
                                   'chart_measure': 'total_miles_traveled',
                                   'chart_time_frame': 36})

        chart_time_frame = monthdelta(datetime.datetime.now().date(), defualt_chart_time_frame)

        all_chart_data = [report for report in
                          vanpool_report.objects.filter(organization_id=user_organization_id).order_by('organization',
                                                                                                       'report_year',
                                                                                                       'report_month').all() if
                          chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]

        chart_label = [report.report_year_month_label for report
                       in all_chart_data]
        chart_label = list(dict.fromkeys(chart_label))
        chart_label = list(dict.fromkeys(chart_label))

        chart_dataset = [report for report in
                         vanpool_report.objects.filter(organization_id=user_organization_id).order_by('organization', 'report_year',
                                                                                     'report_month').all() if
                         chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
        chart_dataset = [getattr(report, form.initial.get('chart_measure')) for report in chart_dataset]

        chart_datasets_filtered = {
            organization.objects.get(id=user_organization_id).name: [json.dumps(list(chart_dataset)), get_color(0)]}

        chart_title = form.MEASURE_CHOICES_DICT[form.initial.get('chart_measure')]
        return render(request, 'pages/Vanpool_data.html', {'form': form,
                                                           'chart_title': chart_title,
                                                           'chart_measure': form.initial.get('chart_measure'),
                                                           'chart_label': chart_label,
                                                           'chart_datasets_filtered': chart_datasets_filtered,
                                                           'org_list': [user_organization_id]})


@login_required(login_url='/Panacea/login')
def Vanpool_other(request):
    return render(request, 'pages/Vanpool_other.html', {})


@login_required(login_url='/Panacea/login')
def UserProfile(request):
    user_name = request.user.get_full_name()
    form_custom_user = user_profile_custom_user(instance=request.user)
    profile_data = profile.objects.get(custom_user=request.user.id)
    form_profile = user_profile_profile(instance=profile_data)
    user_org = profile_data.organization.name

    if request.POST:
        form_custom_user = user_profile_custom_user(data=request.POST.copy(), instance=request.user)
        form_profile = user_profile_profile(data=request.POST.copy(), instance=profile_data)
        if form_custom_user.is_valid() & form_profile.is_valid():
            form_custom_user.save()
            form_profile.save()
            return redirect('UserProfile')
        else:
            form_custom_user.data['first_name'] = request.user.first_name
            form_custom_user.data['last_name'] = request.user.last_name
            form_profile.data['telephone_number'] = profile_data.telephone_number

    return render(request, 'pages/UserProfile.html', {'user_name': user_name,
                                                      'form_custom_user': form_custom_user,
                                                      'form_profile': form_profile,
                                                      'user_org': user_org})


@login_required(login_url='/Panacea/login')
def OrganizationProfile(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_name = org.name
    form = organization_profile(instance=org)
    if request.POST:
        form = organization_profile(data=request.POST.copy(), instance=org)
        if form.is_valid():
            if not 'state' in form.data:
                print(user_profile_data.organization.state)
                form.data['state'] = user_profile_data.organization.state
                print(form.data['state'])
            form.save()
            return redirect('OrganizationProfile')
        else:
            form.data['name'] = org.name
            form.data['address_line_1'] = org.address_line_1
            form.data['address_line_2'] = org.address_line_2
            form.data['city'] = org.city
            # form.data['state'] = org.state
            form.data['zip_code'] = org.zip_code
            form.data['vanshare_program'] = org.vanshare_program

    return render(request, 'pages/OrganizationProfile.html', {'org_name': org_name, 'form': form})


@login_required(login_url='/Panacea/login')
def Permissions(request):
    return render(request, 'pages/Permissions.html', {})


@login_required(login_url='/Panacea/login')
def Admin_reports(request):
    return render(request, 'pages/AdminReports.html', {})


@login_required(login_url='/Panacea/login')
def Admin_ReminderEmail(request):
    return render(request, 'pages/ReminderEmail.html', {})


@login_required(login_url='/Panacea/login')
def Admin_assignPermissions(request):
    profile_data = profile.objects.all()

    Admin_assignPermissions_all = modelformset_factory(custom_user, change_user_permissions_group, extra=0)
    if request.method == 'POST':
        formset = Admin_assignPermissions_all(request.POST)
        # if formset.is_valid():
        #     formset.save()
        #     return JsonResponse({'success': True})
        # else:
        for form in formset:
            if form.is_valid():
                if len(form.changed_data) > 0:
                    data = form.cleaned_data
                    email = data['email']
                    this_user_id = custom_user.objects.get(email=email).id
                    my_profile = profile.objects.get(custom_user_id=this_user_id)
                    my_profile.profile_complete = True
                    my_profile.save()
                    print(email)
                form.save()

        return JsonResponse({'success': True})
    else:
        formset = Admin_assignPermissions_all(queryset=custom_user.objects.filter(id__in=profile_data.values_list('custom_user_id')))
        return render(request, 'pages/AssignPermissions.html', {'Admin_assignPermissions_all': formset, 'profile_data': profile_data})


@login_required(login_url='/Panacea/login')
def accessibility(request):
    return render(request, 'pages/accessibility.html', {})


@login_required(login_url='/Panacea/login')
def public_disclosure(request):
    return render(request, 'pages/PublicDisclosure.html', {})


@login_required(login_url='/Panacea/login')
def Help(request):
    return render(request, 'pages/Help.html', {})


@login_required(login_url='/Panacea/login')
def logout_view(request):
    logout(request)

