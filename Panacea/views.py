import decimal
import json

from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Min, Max, Value, Sum, Avg
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
from .tasks import profile_created
from django.core.exceptions import ValidationError
from django.forms.widgets import CheckboxInput
from .utilities import monthdelta, get_wsdot_color
from django.http import Http404

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
    Modify_A_Vanpool_Expansion
from django.utils.translation import ugettext_lazy as _
from .models import profile, vanpool_report, custom_user,  vanpool_expansion_analysis, organization


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
    if current_user_profile.profile_complete is True:
        return render(request, 'pages/dashboard.html')
    elif current_user_profile.profile_submitted is True:
        return render(request, 'pages/ProfileComplete.html')
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
                profile_created.delay(request.user.id)
                return JsonResponse({'redirect': '../dashboard'})
            else:
                return JsonResponse({'error': form.errors})


@login_required(login_url='/Panacea/login')
def handler404(request, exception):
    return render(request,'pages/error_404.html', status = 404)


@login_required(login_url='/Panacea/login')
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
        form = VanpoolMonthlyReport(user_organization=user_organization,
                                    data=request.POST,
                                    instance=form_data,
                                    record_id=form_data.id,
                                    report_month=month,
                                    report_year=year)
        if form.is_valid():
            form.save()
            successful_submit = True  # Triggers a modal that says the form was submitted
            new_report = False

        #TODO Fix this show it shows the form
        else:
            form = VanpoolMonthlyReport(user_organization=user_organization,
                                        data=request.POST,
                                        instance=form_data,
                                        record_id=form_data.id,
                                        report_month=month,
                                        report_year=year)
            successful_submit = False

    # If not POST
    else:
        form = VanpoolMonthlyReport(user_organization=user_organization,
                                    instance=form_data,
                                    record_id=form_data.id,
                                    report_month=month,
                                    report_year=year)
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
def Vanpool_expansion_submission(request):
    if request.method == 'POST':
        form = submit_a_new_vanpool_expansion(request.POST)
        if form.is_valid():
            form.save()
            # TODO Do you use AJAX on this - What is this for?
            return JsonResponse({'redirect': '../Expansion/'})
        else:
            return render(request, 'pages/Vanpool_expansion_submission.html', {'form':form})
    else:
        form = submit_a_new_vanpool_expansion()
    return render(request, 'pages/Vanpool_expansion_submission.html', {'form': form})


@login_required(login_url='/Panacea/login')
def Vanpool_expansion_analysis(request):
    # pulls the latest vanpool data
    orgs = vanpool_expansion_analysis.objects.filter(expired = False).values('organization_id')
    organization_name = organization.objects.filter(id__in=orgs).values('name')
    vp = vanpool_report.objects.all()
    pv = vp.filter(organization_id__in = orgs, organization = OuterRef('organization'), report_month__isnull = False, vanpool_groups_in_operation__isnull=False).order_by('-id').values('id')
    latest_vanpool = vp.annotate(latest = Subquery(pv[:1])).filter(id = F('latest')).values('report_year', 'report_month', 'vanpool_groups_in_operation', 'organization_id').order_by('organization_id')
    print(latest_vanpool)
    # filters out the max vanpool
    award_date = vanpool_expansion_analysis.objects.filter(expired=False).dates('date_of_award', 'month')
    award_date = award_date[0]
    award_month = award_date.month
    award_year = award_date.year
    van_max = vanpool_report.objects.filter(organization_id__in= orgs, report_year__gte=award_year,report_month__gte=award_month).values('organization').annotate(max_van = Max('vanpool_groups_in_operation')).order_by('organization')
    van_max_list = []
    # had to use a for loop since there's nothing easier really
    for i in van_max:
        vpr = vanpool_report.objects.filter(organization_id = i['organization'], vanpool_groups_in_operation = i['max_van'], report_year__gte=award_year,report_month__gte=award_month).values('id','report_year', 'report_month', 'vanpool_groups_in_operation')
        if len(vpr) > 1:
            vpr = vpr.latest('id')
            van_max_list.append(vpr)
        else:
            van_max_list.append(vpr[0])
    vea = vanpool_expansion_analysis.objects.filter(expired = False).order_by('organization_id')
    vea2 = vanpool_expansion_analysis.objects.filter(expired = False).values('latest_vehicle_acceptance').order_by('organization_id')
    # this bit does some logic to ascertain the remaining months and the deadline

    # this is a method for calculating the deadline and how many months remain
    acceptance_list = []
    for j in vea2:
        result_dic = {}
        latest_date = j['latest_vehicle_acceptance']
        latest_date =latest_date + relativedelta(months=+18)
        r = relativedelta(latest_date, datetime.date.today())
        remaining_months = r.months

        result_dic['latest_date'] = latest_date
        result_dic['remaining_months'] = remaining_months
        acceptance_list.append(result_dic)

    # this is a method for calculating the date when the service expansion was met
    vanexpand = vanpool_expansion_analysis.objects.filter(expired=False).order_by('organization_id').values('date_of_award', 'expansion_vans_awarded', 'vanpools_in_service_at_time_of_award', 'organization_id')
    expansion_goal = []
    for org in vanexpand:
        award_month = org['date_of_award'].month
        award_year = org['date_of_award'].year
        goal = round(org['expansion_vans_awarded']*.8, 0) + org['vanpools_in_service_at_time_of_award']
        org_id = org['organization_id']
        goal = vanpool_report.objects.filter(organization_id = org_id, report_year__gte=award_year,report_month__gte=award_month, vanpool_groups_in_operation__gte=goal).values('id','report_year', 'report_month', 'vanpool_groups_in_operation', 'organization_id')
        if goal.exists():
            expansion_goal.append(goal.earliest('id'))
        else:
            expansion_goal.append('')

    # put them in an iterator to move
    current_biennium = vea
    zipped = zip(organization_name, latest_vanpool, van_max_list, vea, acceptance_list, expansion_goal)
    return render(request, 'pages/Vanpool_expansion.html', {'zipped_data': zipped, 'current_biennium': current_biennium})


@login_required(login_url='/Panacea/login')
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
            form.save()
            successful_submit = True
        else:
            successful_submit = False
    else:
        form = Modify_A_Vanpool_Expansion(instance=form_data)
        successful_submit = False

    zipped = zip(organization_name, vea)
    return render(request, 'pages/Vanpool_expansion_modify.html', {'zipped':zipped, 'id': id, 'form':form, 'successful_submit': successful_submit})


@login_required(login_url='/Panacea/login')
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