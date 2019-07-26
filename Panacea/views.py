import calendar
import decimal
import json

from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Value, Sum, Avg, Count
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
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.db.models import Max, Subquery, F, OuterRef
from django.db.models.expressions import RawSQL
from dateutil.relativedelta import relativedelta
import datetime

from Panacea.decorators import group_required
from .tasks import profile_created
from django.core.exceptions import ValidationError
from django.forms.widgets import CheckboxInput
from .utilities import monthdelta, get_wsdot_color, green_house_gas_per_vanpool_mile, green_house_gas_per_sov_mile
from django.http import Http404
from .filters import VanpoolExpansionFilter
from django.conf import settings

from .forms import CustomUserCreationForm, \
    custom_user_ChangeForm, \
    PhoneOrgSetup, \
    ReportSelection, \
    VanpoolMonthlyReport, \
    user_profile_custom_user, \
    user_profile_profile, \
    organization_profile, \
    change_user_permissions_group, \
    chart_form, \
    submit_a_new_vanpool_expansion, \
    Modify_A_Vanpool_Expansion, \
    request_user_permissions, \
    statewide_summary_settings, \
    Modify_A_Vanpool_Expansion
from django.utils.translation import ugettext_lazy as _
from .models import profile, vanpool_report, custom_user,  vanpool_expansion_analysis, organization
from django.contrib.auth.models import Group
from .utilities import calculate_latest_vanpool, find_maximum_vanpool, calculate_remaining_months, calculate_if_goal_has_been_reached


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
    current_user_profile = profile.objects.get(custom_user=request.user)

    # If the user is registered and has had permissions assigned
    if current_user_profile.profile_complete is True:
        current_user_id = request.user.id
        user_org_id = profile.objects.get(custom_user_id=current_user_id).organization_id
        recent_vanpool_report = vanpool_report.objects. \
            filter(organization_id=user_org_id, report_date__isnull=False). \
            order_by('-report_year', '-report_month').first()
        report_month = recent_vanpool_report.report_month
        previous_report_year = recent_vanpool_report.report_year - 1
        last_year_report = vanpool_report.objects.get(organization_id=user_org_id,
                                                      report_year=previous_report_year,
                                                      report_month=report_month)

        def get_most_recent_and_change(measure):
            """Return a list where first item is the current months stat and the second item is the year over year grouwth"""
            current_monthly_stat = getattr(recent_vanpool_report, measure)
            last_year_stat = getattr(last_year_report, measure)
            if last_year_stat is None:
                year_over_year_growth = "NA"
            else:
                year_over_year_growth = (current_monthly_stat/last_year_stat) - 1

            return [current_monthly_stat, year_over_year_growth]

        def check_status():
            """Returns the report status (if it is past due) of the report for the report after the most recent report"""
            def get_month_year_addition(month):
                if month == 12:
                    return -11, 1
                else:
                    return 1, 0
            month_add, year_add = get_month_year_addition(recent_vanpool_report.report_month)
            next_vanpool_report_status = vanpool_report.objects.get(organization_id=user_org_id,
                                                                    report_month=recent_vanpool_report.report_month + month_add,
                                                                    report_year=recent_vanpool_report.report_year + year_add).status
            return next_vanpool_report_status
        return render(request, 'pages/dashboard.html', {
            'groups_in_operation': get_most_recent_and_change("total_groups_in_operation"),
            'total_passenger_trips': get_most_recent_and_change("total_passenger_trips"),
            'average_riders_per_van': get_most_recent_and_change("average_riders_per_van"),
            'total_miles_traveled': get_most_recent_and_change("total_miles_traveled"),
            'report_status': check_status()
        })

    # If the user has completed their profile but has not had permissions assigned
    elif current_user_profile.profile_submitted is True:
        return render(request, 'pages/ProfileComplete.html')

    # If the user is a new user
    else:
        return redirect('ProfileSetup')


# TODO rename forms to not be camel case
@login_required(login_url='/Panacea/login')
def ProfileSetup(request):
    user_change_form = custom_user_ChangeForm(instance=request.user)
    current_user_instance = profile.objects.get(custom_user=request.user.id)
    phone_org_form = PhoneOrgSetup(instance=current_user_instance)
    report_selection_form = ReportSelection(instance=current_user_instance)
    return render(request, 'pages/ProfileSetup.html', {'ProfileSetup_PhoneAndOrg': phone_org_form,
                                                       'custom_user_ChangeForm': user_change_form,
                                                       'ProfileSetup_ReportSelection': report_selection_form})


@login_required(login_url='/Panacea/login')
def ProfileSetup_Review(request):
    if request.method == 'POST':
        current_user = request.user
        if request.POST:
            form = custom_user_ChangeForm(request.POST, instance=current_user)
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
        current_user_instance = profile.objects.get(custom_user=request.user.id)
        if request.POST:
            form = PhoneOrgSetup(request.POST, instance=current_user_instance)
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
        current_user_instance = profile.objects.get(custom_user=request.user.id)
        if request.POST:
            form = ReportSelection(request.POST, instance=current_user_instance)
            if form.is_valid():
                # form.user = request.user
                form.save()
                current_user_instance.profile_submitted = True
                current_user_instance.save()
                emailRecipient = custom_user.objects.filter(id = request.user.id).values('first_name','last_name')
                name = emailRecipient.values_list('first_name', flat=True)
                emailAddress = custom_user.objects.filter(id = request.user.id).values_list('email', flat = True)
                msg_plain = render_to_string('emails/registration_email.txt', {'firstname':name[0]})
                msg_html = render_to_string('emails/registration_email.html', {'firstname': name[0]})
                send_mail('Welcome to WSDOT\'s Public Transit Data Reporting Portal', msg_plain, settings.EMAIL_HOST_USER, [emailAddress[0]], html_message=msg_html,)
                return JsonResponse({'redirect': '../dashboard'})
            else:
                return JsonResponse({'error': form.errors})


@login_required(login_url='/Panacea/login')
def handler404(request, exception):
    return render(request, 'pages/error_404.html', status = 404)


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter')
def Vanpool_report(request, year=None, month=None):
    # Set form parameters
    user_organization_id = profile.objects.get(custom_user_id=request.user.id).organization_id
    user_organization = organization.objects.get(id=user_organization_id)
    organization_data = vanpool_report.objects.filter(organization_id=user_organization_id)

    # logic to select the most recent form or the form requested through the URL
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

    # Logic to hide year selectors
    min_year = organization_data.all().aggregate(Min('report_year')).get('report_year__min') == year
    max_year = organization_data.all().aggregate(Max('report_year')).get('report_year__max') == year

    # TODO rename to something better (this populates the navigation table)
    past_report_data = vanpool_report.objects.filter(organization_id=user_organization_id, report_year=year)

    # Instance data to link form to data
    form_data = vanpool_report.objects.get(organization_id=user_organization_id, report_year=year, report_month=month)

    # TODO convert to django message framework
    # Logic if form is a new report or is an existing report (Comments are needed before editing an existing reports)
    if form_data.report_date is None:
        new_report = True
    else:
        new_report = False

    # Respond to POST request
    if request.method == 'POST':
        form = VanpoolMonthlyReport(user_organization = user_organization, data=request.POST, instance=form_data, record_id = form_data.id, report_month=month, report_year=year)
        if form.is_valid():
            form.save()
            successful_submit = True  # Triggers a modal that says the form was submitted
            new_report = False

        #TODO Fix this show it shows the form
        else:
            form = VanpoolMonthlyReport(user_organization=user_organization, data=request.POST, instance=form_data,
                                        record_id=form_data.id, report_month=month, report_year=year)
            successful_submit = False

    # If not POST
    else:
        form = VanpoolMonthlyReport(user_organization=user_organization, instance=form_data, record_id = form_data.id, report_month=month, report_year=year)
        successful_submit = False

    if new_report == False:
        form.fields['changeReason'].required = True
    else:
        form.fields['changeReason'].required = False

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
@group_required('WSDOT staff')
def Vanpool_expansion_submission(request):
    if request.method == 'POST':
        form = submit_a_new_vanpool_expansion(data = request.POST)
        if form.is_valid():
            instance = form.save(commit = False)
            instance.deadline = instance.latest_vehicle_acceptance + relativedelta(months=+18)
            instance.expansion_goal = int(round(instance.expansion_vans_awarded * .8, 0) + \
                                                      instance.vanpools_in_service_at_time_of_award)
            instance.expired = False
            instance.vanpool_goal_met = False
            instance.extension_granted = False
            instance.save()
            # the redirect here is to the expansion page, which triggers the sqlite queries to populate the rest of the data
            return JsonResponse({'redirect': '../Expansion/'})
        else:
            return render(request, 'pages/Vanpool_expansion_submission.html', {'form':form})
    else:
        form = submit_a_new_vanpool_expansion(data=request.POST)
    return render(request, 'pages/Vanpool_expansion_submission.html', {'form': form})


@login_required(login_url='/Panacea/login')
def Vanpool_expansion_analysis(request):
    # pulls the latest vanpool data
    calculate_latest_vanpool()
    find_maximum_vanpool()
    calculate_remaining_months()
    calculate_if_goal_has_been_reached()
    f = VanpoolExpansionFilter(request.GET, queryset=vanpool_expansion_analysis.objects.all())
    return render(request, 'pages/Vanpool_expansion.html', {'filter': f})


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def Vanpool_expansion_modify(request, id=None):
    if not id:
        id = 1
    orgs = vanpool_expansion_analysis.objects.filter(expired = False).values('organization_id')
    organization_name = organization.objects.filter(id__in=orgs).values('name')
    vea = vanpool_expansion_analysis.objects.all().filter(expired = False).order_by('organization_id')
    form_data = vanpool_expansion_analysis.objects.get(id = id)

    if request.method == 'POST':
        form = Modify_A_Vanpool_Expansion(data=request.POST, instance=form_data)
        if form.is_valid():
            form.cleaned_data['deadline'] = form.cleaned_data['latest_vehicle_acceptance'] + relativedelta(months=+18)
            form.save()
        else:
            form = Modify_A_Vanpool_Expansion(instance=form_data)

    else:
        form = Modify_A_Vanpool_Expansion(instance=form_data)
    zipped = zip(organization_name, vea)
    return render(request, 'pages/Vanpool_expansion_modify.html', {'zipped':zipped, 'id': id, 'form':form})


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter', 'WSDOT staff')
def Vanpool_data(request):

    # If it is a request for a chart
    if request.POST:
        form = chart_form(data=request.POST)
        org_list = request.POST.getlist("chart_organizations")
        chart_time_frame = monthdelta(datetime.datetime.now().date(), form.data['chart_time_frame'])
        chart_measure = form.data['chart_measure']

    # Default chart for first load
    else:
        default_time_frame = 36  # months
        chart_time_frame = monthdelta(datetime.datetime.now().date(), default_time_frame)
        org_list = [profile.objects.get(custom_user_id=request.user.id).organization_id]
        chart_measure = 'total_miles_traveled'
        form = chart_form(initial={'chart_organizations': org_list[0],
                                   'chart_measure': chart_measure,
                                   'chart_time_frame': default_time_frame})

    if form.is_valid:
        # Get data for x axis labels
        all_chart_data = [report for report in vanpool_report.objects.filter(organization_id__in=org_list).order_by('organization', 'report_year', 'report_month').all() if
                          chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
        x_axis_labels = [report.report_year_month_label for report in all_chart_data]
        x_axis_labels = list(dict.fromkeys(x_axis_labels))

        # Get datasets in the format chart.js needs
        chart_datasets = {}
        color_i = 0
        for org in org_list:
            chart_dataset = [report for report in vanpool_report.objects.filter(organization_id=org).order_by('organization', 'report_year', 'report_month').all() if
                             chart_time_frame <= report.report_due_date <= datetime.datetime.today().date()]
            chart_dataset = [getattr(report, chart_measure) for report in chart_dataset]
            chart_datasets[organization.objects.get(id=org).name] = [json.dumps(list(chart_dataset)), get_wsdot_color(color_i)]
            color_i = color_i + 1

        # Set chart title
        chart_title = form.MEASURE_CHOICES_DICT[chart_measure]

        return render(request, 'pages/Vanpool_data.html', {'form': form,
                                                           'chart_title': chart_title,
                                                           'chart_measure': chart_measure,
                                                           'chart_label': x_axis_labels,
                                                           'chart_datasets_filtered': chart_datasets,
                                                           'org_list': org_list
                                                           })
    else:
        raise Http404


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter', 'WSDOT staff')
def vanpool_statewide_summary(request):

    MEASURES = [
        ("vanpool_miles_traveled", "vanshare_miles_traveled"),
        ("vanpool_passenger_trips", "vanshare_passenger_trips"),
        ("vanpool_groups_in_operation", "vanshare_groups_in_operation"),
    ]

    if request.POST:
        settings_form = statewide_summary_settings(data=request.POST)
        include_agency_classifications = request.POST.getlist("include_agency_classifications")
        include_years = int(settings_form.data['include_years'])
        include_regions = settings_form.data['include_regions']

    else:
        include_years = 3
        include_regions = "Statewide"
        include_agency_classifications = [classification[0] for classification in organization.AGENCY_CLASSIFICATIONS]

        settings_form = statewide_summary_settings(initial={
            "include_years": include_years,
            "include_regions": include_regions,
            "include_agency_classifications": include_agency_classifications
        })

    if settings_form.is_valid:
        all_chart_data = [report for report in
                          vanpool_report.objects.order_by('report_year', 'report_month').all() if
                          report.report_year >= datetime.datetime.today().year - include_years]
        x_axis_labels = [report.report_month for report in all_chart_data]
        x_axis_labels = list(dict.fromkeys(x_axis_labels))
        x_axis_labels = list(map(lambda x: calendar.month_name[x], x_axis_labels))


        if include_regions != "Statewide":
            if include_regions == "Puget Sound":
                orgs_to_include = organization.objects.filter(classification__in=include_agency_classifications).filter(
                    in_puget_sound_area=True).values_list('id')
            else:
                orgs_to_include = organization.objects.filter(classification__in=include_agency_classifications).filter(
                    in_puget_sound_area=False).values_list('id')
        else:
            orgs_to_include = organization.objects.filter(classification__in=include_agency_classifications).values_list('id')

        years = range(datetime.datetime.today().year - include_years + 1, datetime.datetime.today().year + 1)

        all_data = vanpool_report.objects.filter(report_year__gte=datetime.datetime.today().year - (include_years - 1),
                                                 report_year__lte=datetime.datetime.today().year,
                                                 organization_id__in=orgs_to_include).order_by('report_year',
                                                                                               'report_month').all()

        # TODO once the final data is in we need to confirm that the greenhouse gas calculations are correct
        summary_table_data = vanpool_report.objects.filter(report_year__gte=datetime.datetime.today().year - (include_years - 1),
                                                           report_year__lte=datetime.datetime.today().year,
                                                           organization_id__in=orgs_to_include,
                                                           report_date__isnull=False,
                                                           vanpool_passenger_trips__isnull=False).values('report_year').annotate(
            table_total_miles_traveled=Sum(F(MEASURES[0][0]) + F(MEASURES[0][1])),
            table_total_passenger_trips=Sum(F(MEASURES[1][0]) + F(MEASURES[2][1])),
            table_total_groups_in_operation=Sum(F(MEASURES[2][0]) + F(MEASURES[2][1])) / Count('report_month', distinct=True),
            green_house_gas_prevented=Sum((F(MEASURES[0][0]) + F(MEASURES[0][1])) * (F('average_riders_per_van') - 1)) * green_house_gas_per_sov_mile() - Sum(F(MEASURES[0][0]) + F(MEASURES[0][1])) * green_house_gas_per_vanpool_mile()
        )

        # TODO once the final data is in we need to confirm that the greenhouse gas calculations are correct
        summary_table_data_total = vanpool_report.objects.filter(report_year__gte=datetime.datetime.today().year - (include_years - 1),
                                                                 report_year__lte=datetime.datetime.today().year,
                                                                 organization_id__in=orgs_to_include).aggregate(
            table_total_miles_traveled=Sum(F(MEASURES[0][0]) + F(MEASURES[0][1])),
            table_total_passenger_trips=Sum(F(MEASURES[1][0]) + F(MEASURES[2][1])),
            green_house_gas_prevented=Sum((F(MEASURES[0][0]) + F(MEASURES[0][1])) * (
                    F('average_riders_per_van') - 1)) * green_house_gas_per_sov_mile() - Sum(
                F(MEASURES[0][0]) + F(MEASURES[0][1])) * green_house_gas_per_vanpool_mile()
        )

        all_charts = list()
        for i in range(len(MEASURES) + 1):
            # to include green house gasses
            if i == len(MEASURES):
                all_chart_data = all_data.values('report_year', 'report_month').annotate(
                    result=Sum((F(MEASURES[0][0]) + F(MEASURES[0][1])) * (F('average_riders_per_van') - 1)) * green_house_gas_per_sov_mile() - Sum(F(MEASURES[0][0]) + F(MEASURES[0][1])) * green_house_gas_per_vanpool_mile()
                )
            else:
                all_chart_data = all_data.values('report_year', 'report_month').annotate(
                    result=Sum(F(MEASURES[i][0]) + F(MEASURES[i][1]))
                )

            chart_datasets = {}
            color_i = 0
            for year in years:
                if year == datetime.datetime.today().year:
                    current_year = True
                    line_color = get_wsdot_color(color_i, hex_or_rgb='rgb')
                else:
                    current_year = False
                    line_color = get_wsdot_color(color_i, alpha=50, hex_or_rgb='rgb')
                chart_dataset = all_chart_data.filter(report_year=year)
                if chart_dataset.count() >= 1:
                    chart_dataset = [result["result"] for result in chart_dataset]
                    chart_datasets[year] = [json.dumps(list(chart_dataset)), line_color, current_year]
                    color_i = color_i + 1

            all_charts.append(chart_datasets)

    return render(request, 'pages/vanpool_statewide_summary.html', {'settings_form': settings_form,
                                                                    'chart_label': x_axis_labels,
                                                                    'all_charts': all_charts,
                                                                    'summary_table_data': summary_table_data,
                                                                    'summary_table_data_total': summary_table_data_total,
                                                                    'include_regions': include_regions,
                                                                    'include_agency_classifications': include_agency_classifications
                                                                    }
                  )


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
def OrganizationProfileUsers(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_id = organization.objects.filter(name=org).values('id')
    org_id = org_id[0]['id']
    # TODO could this be valueslist?
    vals = profile.objects.filter(organization_id=org_id).values('custom_user')
    vals = [i['custom_user'] for i in vals]
    cust = custom_user.objects.filter(id__in=vals).values('first_name', 'last_name', 'email', 'date_joined', 'last_login')
    org_name = org.name
    return render(request, 'pages/OrganizationProfileUsers.html', {'org_name': org_name, 'users': cust})


@login_required(login_url='/Panacea/login')
@group_required('Vanpool reporter', 'WSDOT staff', 'Summary reporter')
def OrganizationProfile(request):
    user_profile_data = profile.objects.get(custom_user=request.user.id)
    org = user_profile_data.organization
    org_name = org.name
    form = organization_profile(instance=org)
    if request.POST:
        form = organization_profile(data=request.POST.copy(), instance=org)
        if form.is_valid():
            # TODO figure out why is this here
            if not 'state' in form.data:
                form.data['state'] = user_profile_data.organization.state
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
    submit_success = False
    if request.POST:
        form = request_user_permissions(data=request.POST)
        if form.is_valid():

            groups = ' & '.join(str(s[1]) for s in form.cleaned_data['groups'].values_list())

            msg_html = render_to_string('emails/request_permissions_email.html',
                                        {'user_name': request.user.get_full_name(), 'groups': groups})
            msg_plain = render_to_string('emails/request_permissions_email.txt',
                                         {'user_name': request.user.get_full_name(), 'groups': groups})
            send_mail(
                subject='Permissions Request - Public Transportation Reporting Portal',
                message=msg_plain,
                from_email='some@sender.com',  # TODO change this to the correct email address
                recipient_list=['wesleyi@wsdot.wa.gov', ],  # TODO change this to the correct email address
                html_message=msg_html,
            )
            msg_html = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
            msg_plain = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
            send_mail(
                subject='Active Permissions Request - Public Transportation Reporting Portal',
                message=msg_plain,
                from_email='some@sender.com',  # TODO change this to the correct email address
                recipient_list=['wesleyi@wsdot.wa.gov', ],  # TODO change this to the correct email address
                html_message=msg_html,
            )
            current_user_profile = profile.objects.get(custom_user_id=request.user.id)
            current_user_profile.requested_permissions.set(form.cleaned_data['groups'])
            current_user_profile.active_permissions_request = True
            current_user_profile.save()
            submit_success = True

    user = request.user
    auth_groups = Group.objects.all()
    form = request_user_permissions(instance=user)

    return render(request, 'pages/Permissions.html', {'auth_groups': auth_groups,
                                                      'user_name': request.user.get_full_name(),
                                                      'form': form,
                                                      'submit_success': submit_success})


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def Admin_reports(request):
    return render(request, 'pages/AdminReports.html', {})


@login_required(login_url='/Panacea/login')
@group_required('WSDOT staff')
def Admin_ReminderEmail(request):
    return render(request, 'pages/ReminderEmail.html', {})


@login_required(login_url='/Panacea/login')
# @group_required('WSDOT staff')
def Admin_assignPermissions(request, active=None):
    if not active:
        active = 'active'
    active_requests = profile.objects.filter(active_permissions_request=True).exists()
    if active_requests and active == 'active':
        profile_data = profile.objects.filter(active_permissions_request=True).all()
    else:
        profile_data = profile.objects.all()

    assign_permissions_formset = modelformset_factory(custom_user, change_user_permissions_group, extra=0)

    if request.method == 'POST':
        formset = assign_permissions_formset(request.POST)
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
                    my_profile.active_permissions_request = False
                    my_profile.save()
                    # print(email)
                form.save()

        return JsonResponse({'success': True})
    else:
        formset = assign_permissions_formset(queryset=custom_user.objects.filter(id__in=profile_data.values_list('custom_user_id')))
        if active_requests and active == 'active':
            return render(request, 'pages/assign_permissions_active_requests.html', {'Admin_assignPermissions_all': formset,
                                                                                     'profile_data': profile_data})
        else:
            return render(request, 'pages/AssignPermissions.html', {'Admin_assignPermissions_all': formset,
                                                                    'profile_data': profile_data,
                                                                    'active_requests': active_requests})


@login_required(login_url='/Panacea/login')
def accessibility(request):
    return render(request, 'pages/accessibility.html', {})


@login_required(login_url='/Panacea/login')
def public_disclosure(request):
    return render(request, 'pages/PublicDisclosure.html', {})


@login_required(login_url='/Panacea/login')
def help_page(request):
    return render(request, 'pages/Help.html', {})


@login_required(login_url='/Panacea/login')
def logout_view(request):
    logout(request)


# TODO move to utilities.py
def percent_change_calculation(totals, label):
    percent_change = []
    count = 0
    # calculating the percent change in this for loop because its messy as hell otherwise
    for idx, val in enumerate(totals):
        if count == 0:
            percent_change.append('N/A')
            count += 1
        else:
            try:
                percent = round(((val[label] - totals[idx - 1][label]) / totals[idx - 1][label]) * 100, 2)
                percent_change.append(percent)
            except ZeroDivisionError:
                percent_change.append('N/A')
    return percent_change


@login_required(login_url='/Panacea/login')
def Operation_Summary(request):
    total_vp = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_groups_in_operation')).filter(report_month=12, vanpool_groups_in_operation__isnull=False)
    years = [i['report_year'] for i in total_vp]
    print(years)
    total_vp = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_groups_in_operation')).filter(report_month = 12, vanpool_groups_in_operation__isnull=False)
    vp_percent_change = percent_change_calculation(total_vp, 'vanpool_groups_in_operation__sum')
    total_vs =vanpool_report.objects.values('report_year').annotate(Sum('vanshare_groups_in_operation')).filter(report_month = 12, vanshare_groups_in_operation__isnull=False)
    vs_percent_change = percent_change_calculation(total_vs, 'vanshare_groups_in_operation__sum')
    total_starts = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_group_starts')).filter(vanpool_groups_in_operation__isnull=False)
    starts_percent_change = percent_change_calculation(total_starts, 'vanpool_group_starts__sum')
    total_folds = vanpool_report.objects.values('report_year').annotate(Sum('vanpool_group_folds')).filter(vanpool_groups_in_operation__isnull=False)
    folds_percent_change = percent_change_calculation(total_folds, 'vanpool_group_folds__sum')
    zipped = zip(total_starts, total_vp)
    starts_as_a_percent = []
    for i in zipped:
        percent = round((i[0]['vanpool_group_starts__sum']/i[1]['vanpool_groups_in_operation__sum'])*100, 2)
        starts_as_a_percent.append(percent)
    folds_as_a_percent = []
    zipped = zip(total_folds, total_vp)
    for i in zipped:
        percent = round((i[0]['vanpool_group_folds__sum']/i[1]['vanpool_groups_in_operation__sum'])*100, 2)
        folds_as_a_percent.append(percent)
    zipped = zip(total_starts, total_folds)
    net_vanpool = []
    for start, fold in zipped:
        net_vanpool.append(start['vanpool_group_starts__sum'] - fold['vanpool_group_folds__sum'])
    avg_riders = vanpool_report.objects.values('report_year').annotate(Avg('average_riders_per_van')).filter(vanpool_groups_in_operation__isnull=False)
    avg_miles = vanpool_report.objects.values('report_year').annotate(Avg('average_round_trip_miles')).filter(vanpool_groups_in_operation__isnull=False)
    print(avg_riders)
    print(avg_miles)
    vp_totals = zip(total_vp, vp_percent_change)
    vs_totals = zip(total_vs, vs_percent_change)
    starts = zip(total_starts, starts_percent_change)
    folds = zip(total_folds, folds_percent_change)
    empty_list = ['']*len(total_vp)
    starts_as_percent = zip(starts_as_a_percent, empty_list)
    folds_as_percent = zip(folds_as_a_percent, empty_list)
    net_vans = zip(net_vanpool, empty_list)
    average_riders = zip(avg_riders, empty_list)
    average_miles = zip(avg_miles, empty_list)

    return render(request, 'pages/OperationSummary.html', {'vp_totals': vp_totals, 'vs_totals': vs_totals, 'starts':starts, 'folds': folds, 'starts_as_a_percent': starts_as_percent,
                                                           'folds_as_percent': folds_as_percent, 'net_vans': net_vans, 'average_riders': average_riders, 'average_miles': average_miles, 'years':years})


@login_required(login_url='/Panacea/login')
def Vanpool_Growth(request):

    return render(request, 'pages/VanpoolGrowth.html', {})