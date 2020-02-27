import calendar
import json

from django.db import transaction
from django_pandas.io import read_frame
import pandas as pd
import numpy as np
from .models import revenue_source, organization, vanpool_expansion_analysis, vanpool_report, profile, transit_data, \
    service_offered, transit_mode, revenue, expense, depreciation, fund_balance, stylesheets,  summary_organization_progress, summary_report_status
from django.db.models import Max, Subquery, F, OuterRef, Case, CharField, Value, When, Sum, Count, Avg, FloatField, \
    ExpressionWrapper, Q
from django.db.models.functions import Coalesce

import datetime
from dateutil.relativedelta import relativedelta
#####
# Utility functions
#####

#


def calculate_percent_change(data1, data2):
    percent = (data2 - data1)/data1
    percent = percent*100
    return percent


def create_all_summary_report_statuses():
    year = get_current_summary_report_year()
    summary_orgs = organization.objects.filter(summary_reporter = True)
    for org in summary_orgs:
        summary_report_status.objects.get_or_create(year = year, organization = org)


def data_check(year, models_list, summary_reporter_type):
    '''this function creates null value for the purpose of building tables'''




def create_statewide_expense_table(year):
    from .models import depreciation
    df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year=year, transit_metric_id=9).values('organization__name',
    'transit_mode__rollup_mode').annotate(reported_value=Sum('reported_value')))

    depreciation = read_frame(depreciation.objects.filter(year = year).values('organization__name').annotate(reported_value = Sum('reported_value')))
    debt_service = read_frame(fund_balance.objects.filter(organization__summary_organization_classifications_id = 6, year = year, fund_balance_type = 12).values('organization__name').annotate(reported_value = Sum('reported_value')))
    expenses = read_frame(expense.objects.filter(organization__summary_organization_classifications_id =6, year = year, expense_source_id__in = [1,2]).values('expense_source__name', 'organization__name').annotate(reported_value = Sum('reported_value')))
    revenue_capital = read_frame(revenue.objects.filter(organization__summary_organization_classifications_id = 6, year = year, revenue_source__funding_type = 'Capital').values('organization__name').annotate(reported_value = Sum('reported_value')))
    depreciation['data_type'] = 'Depreciation'
    debt_service['data_type'] = 'Debt Service'
    print(depreciation)
    print(debt_service)
    print(expenses)
    print(revenue_capital)










def create_statewide_revenue_table(year):
    revenues = read_frame(revenue.objects.filter(organization__summary_organization_classifications_id=6, year=year,reported_value__isnull=False).values('organization__name',
    'revenue_source_id__government_type','revenue_source_id__funding_type').annotate(reported_value=Sum('reported_value')).exclude(revenue_source_id__in = [63,64]))
    fares = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year = year, reported_value__isnull = False, transit_metric_id = 10, transit_mode_id__in = [1,2,4,5,6,7,8,9,10,11]).values('organization__name').annotate(fare_revenue = Sum('reported_value'))).set_index('organization__name')
    vanpool = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year = year, reported_value__isnull = False, transit_metric_id = 10, transit_mode_id__in = [3]).values('organization__name').annotate(vanpool_revenue = Sum('reported_value'))).set_index('organization__name')

    revenues['title'] = revenues['revenue_source_id__government_type'] + ' ' + revenues['revenue_source_id__funding_type'] + ' Revenue'
    df = revenues.pivot(index = 'organization__name', columns= 'title', values = 'reported_value')
    df = pd.concat([df, fares, vanpool], axis = 1).fillna(0)
    df = df.reset_index()
    subtotal = pd.DataFrame(df[df['index'] != 'Sound Transit'].sum(axis = 0)).transpose()
    subtotal.at[0, 'index'] = 'Sub-Totals'
    total = pd.DataFrame(df.sum(axis = 0)).transpose()
    total.at[0, 'index'] = 'Statewide Revenue Total'
    df = pd.concat([df[df['index'] != 'Sound Transit'], subtotal, df[df['index'] == 'Sound Transit'], total], axis = 0).set_index('index')
    df['Total Revenue'] = df.sum(axis=1)
    df = df.reset_index()
    df = df.rename(columns = {'Local Operating Revenue':'Sales or Local Tax', 'fare_revenue': 'Fare Revenue (all modes except vanpool', 'vanpool_revenue':'Vanpool Revenue', 'index':'Revenues'})
    df = df.reindex(columns = ['Revenues', 'Sales or Local Tax', 'Fare Revenue (all modes except vanpool', 'Vanpool Revenue','Federal Operating Revenue', 'State Operating Revenue', 'Other Operating Revenue','Federal Capital Revenue',
                               'State Capital Revenue', 'Total Revenue'])
    return df


def create_dependent_statistics(df):
    '''associated with generate mode by agency table function'''
    df['Passenger Trips/Revenue Hour'] = df['Passenger Trips']/df['Revenue Vehicle Hours']
    df['Passenger Trips/Revenue Mile'] = df['Passenger Trips']/ df['Revenue Vehicle Hours']
    df['Revenue Hours/FTE'] = df['Revenue Vehicle Hours']/df['Employees - FTEs']
    df['Operating Expenses/Revenue Hour'] = df['Operating Expenses']/df['Revenue Vehicle Hours']
    df['Operating Expenses/ Revenue Mile'] = df['Operating Expenses']/df['Revenue Vehicle Miles']
    df['Operating Expenses/Passenger Trip'] = df['Operating Expenses']/df['Passenger Trips']
    df['Farebox Recovery Ratio'] = df['Farebox Revenues']/df['Operating Expenses']*100
    df = df.replace(np.inf, 0)
    return df

def organization_names_and_classifications(df):
    '''code to add classifications and organization names to the mode by agency table'''
    org_names = df.organization__name.tolist()
    list_of_orgs = organization.objects.filter(name__in=org_names).values('name', 'classification')
    classification_dic = dict(zip([name['name'] for name in list_of_orgs], [name['classification'] for name in list_of_orgs]))
    df['classification'] = df['organization__name'].apply(lambda x: classification_dic[x])
    return df

def sum_and_average_function(category, df):
    '''builds the sum and average rows for each mode'''
    if "Statewide" in category:  # builds statewide version; excludes other aggregate sums and averages
        statewidedf = df[df.classification.isin(['Urban', 'Small Urban', 'Rural'])]
        sums = statewidedf[['Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles', 'Total Vehicle Miles','Passenger Trips', 'Employees - FTEs', 'Operating Expenses', 'Farebox Revenues']].sum()
        avgs = statewidedf[['Passenger Trips/Revenue Hour', 'Passenger Trips/Revenue Mile', 'Revenue Hours/FTE','Operating Expenses/Revenue Hour', 'Operating Expenses/ Revenue Mile','Operating Expenses/Passenger Trip', 'Farebox Recovery Ratio']].mean()
    else:
        sums = df[df.classification == category][['Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles', 'Total Vehicle Miles','Passenger Trips', 'Employees - FTEs', 'Operating Expenses', 'Farebox Revenues']].sum()
        avgs = df[df.classification == category][['Passenger Trips/Revenue Hour', 'Passenger Trips/Revenue Mile', 'Revenue Hours/FTE','Operating Expenses/Revenue Hour', 'Operating Expenses/ Revenue Mile', 'Operating Expenses/Passenger Trip','Farebox Recovery Ratio']].mean()
    changeddf = pd.DataFrame(pd.concat([sums, avgs])).transpose()
    changeddf['classification'] = 'Totals/Averages'
    changeddf['organization__name'] = category
    changeddf = changeddf.set_index('organization__name')
    df = pd.concat([df, changeddf])
    return df


def generate_mode_by_agency_tables(mode, year):
    '''this function generates stats for each transit mode by agency'''
    #TODO condense this, functionalize; figure out what to do about Central Transit
    if mode == 'Demand Response':
        # DR Taxi services is its own mode that gets collapsed in, so have to build some special bits of this
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year=year,
                                                    reported_value__isnull=False, transit_mode__name__in=['Demand Response', 'Demand Response Taxi Services'],
                                                    transit_metric_id__in=[1, 2, 3, 4, 5, 8, 9, 10]).values('organization__name', 'transit_metric__name').annotate(reported_value=Sum('reported_value')))
    else:
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year=year,reported_value__isnull=False, transit_mode__name= mode, transit_metric_id__in=[1, 2, 3, 4, 5, 8, 9, 10]).values('organization__name','transit_metric__name').annotate(reported_value = Sum('reported_value')))
    df = df.pivot(index = 'organization__name', columns = 'transit_metric__name', values = 'reported_value').fillna(0)
    df = df.reset_index()
    df = organization_names_and_classifications(df)
    df = create_dependent_statistics(df)
    df = df.set_index('organization__name')
    if ['Rural'] in df.classification.unique():  # check to see if there's more than one type of agency in the list
        categories = ['Urban', 'Small Urban', 'Rural', 'Statewide {}'.format(mode)]
        for category in categories:
            df = sum_and_average_function(category, df)
    else: # code for the more rarely used modes, where there's only a couple of agencies in a mode, i.e. Commuter Rail, Light Rail
        category = 'Statewide {}'.format(mode)
        df = sum_and_average_function(category, df)
    df = df.reindex(columns = ['classification', 'Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles', 'Total Vehicle Miles', 'Passenger Trips','Employees - FTEs',
                               'Operating Expenses', 'Farebox Revenues','Passenger Trips/Revenue Hour', 'Passenger Trips/Revenue Mile', 'Revenue Hours/FTE', 'Operating Expenses/Revenue Hour',
                               'Operating Expenses/ Revenue Mile', 'Operating Expenses/Passenger Trip', 'Farebox Recovery Ratio'])
    df = df.reset_index()
    heading_list =  df.columns.tolist()
    heading_list = [mode, 'System Category'] + heading_list[2:]
    col_list = df.columns.tolist()
    col_list = [i.replace(' ', '') for i in col_list]
    col_list = [i.replace('/', '') for i in col_list]
    col_list = [i.replace('-FTEs', '') for i in col_list]
    df.columns = col_list
    return df, heading_list


def generate_performance_measure_table(metric, years):
    if len(metric) == 2:
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years,reported_value__isnull=False).values('year', 'rollup_mode__name').annotate(
        reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric[0]))/ Sum('reported_value', filter = Q(transit_metric__name = metric[1]))))
    else:
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years, reported_value__isnull=False).values('year', 'rollup_mode__name').annotate(reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric))))
    df = df.dropna(thresh=3)
    df = df.pivot(index = 'rollup_mode__name', columns = 'year', values= 'reported_value')
    rollup_mode_list = ['Fixed Route', 'Route Deviated', 'Demand Response', 'Vanpool', 'Commuter Rail', 'Light Rail']
    df = df.reindex(rollup_mode_list)
    if metric in ["Revenue Vehicle Hours", 'Revenue Vehicle Miles', 'Passenger Trips', 'Farebox Revenues', 'Operating Expenses']:
        df = df.append(df.sum().rename('Total'))
    if metric == ('Farebox Revenues', 'Operating Expenses'):
        df = df*100
    df = df.reset_index()
    df['percent_change'] = ((df.iloc[:, 6] - df.iloc[:, 5]) / df.iloc[:, 5]) * 100
    df = df.fillna('-')
    df = df.replace(np.inf, 100.00)
    df.columns = ['title', 'year1', 'year2', 'year3', 'year4', 'year5', 'year6', 'percent_change']
    return df





def complete_data():
    latest_data = vanpool_report.objects.filter(vanpool_groups_in_operation__isnull=False).values('report_year','report_month').annotate(Count('id')).order_by('-id__count', '-report_year', '-report_month').first()
    return latest_data



def filter_revenue_sheet_by_classification(classification):
    if classification == 'Transit':
        return 'Transit'
    elif classification == 'Tribe':
        return 'Transit'
    elif classification == 'Community Provider':
        return 'Community Provider'
    elif classification == 'Ferry':
        return 'Ferry'

def find_vanpool_organizations():
    return organization.objects.all().filter(vanpool_program=True)


def generate_summary_report_years():
    currentYear = datetime.date.today().year
    reportYears = [currentYear-3, currentYear-2, currentYear-1]
    return reportYears

def find_user_organization_id(id):
    user_profile_data = profile.objects.get(custom_user=id)
    org = user_profile_data.organization_id
    return org

def find_user_organization(id):
    user_profile_data = profile.objects.get(custom_user=id)
    org = user_profile_data.organization
    return org

def pull_organization(self):
    queryset = organization.objects.all()
    return queryset


def calculate_latest_vanpool():
    latestVanData = vanpool_expansion_analysis.objects.values('id', 'date_of_award', 'deadline', 'organization_id').order_by('organization_id')
    for van in latestVanData:
        print(van)
        awardMonth = van['date_of_award'].month
        awardYear = van['date_of_award'].year
        deadlineYear = van['deadline'].year
        deadlineMonth = van['deadline'].month
        orgId = van['organization_id']
        veaId = van['id']

        dates = vanpool_report.objects.filter(organization_id =orgId,
                   report_month__isnull=False, vanpool_groups_in_operation__gte=0, report_year__gte = awardYear, report_year__lte = deadlineYear).values('id','report_year', 'report_month',
                    'vanpool_groups_in_operation', 'organization_id')
        qs1 = dates.all().filter(report_year = awardYear, report_month__gte = awardMonth)
        qs2 = dates.all().filter(report_year = deadlineYear, report_month__lte = deadlineMonth)
        qs3 = dates.all().filter(report_year__gt = awardYear, report_year__lt = deadlineYear)
        latest_vanpool = qs3.union(qs1, qs2)
        if len(latest_vanpool) > 1:
            latest_vanpool = latest_vanpool.latest('id')
            latestVanDate = datetime.date(latest_vanpool['report_year'], latest_vanpool['report_month'], 1)
            vanpool_expansion_analysis.objects.filter(id=veaId).update(latest_report_date=latestVanDate,
                                                                           latest_vanpool_number=latest_vanpool['vanpool_groups_in_operation'])
        else:
            latestVanDate = datetime.date(latest_vanpool.report_year, latest_vanpool.report_month, 1)
            vanpool_expansion_analysis.objects.filter(id=veaId).update(latest_report_date=latestVanDate,
                                                                           latest_vanpool_number=latest_vanpool.vanpool_groups_in_operation)



def find_maximum_vanpool():
    vanMaxData = vanpool_expansion_analysis.objects.values('id', 'date_of_award', 'deadline', 'organization_id').order_by('organization_id')
    for van in vanMaxData:
        awardMonth = van['date_of_award'].month
        awardYear = van['date_of_award'].year
        deadlineYear = van['deadline'].year
        deadlineMonth = van['deadline'].month
        orgId = van['organization_id']
        dates = vanpool_report.objects.filter(organization_id=orgId,
                                              report_month__isnull=False, vanpool_groups_in_operation__gte=0,
                                              report_year__gte=awardYear, report_year__lte=deadlineYear)
        qs1 = dates.all().filter(report_year=awardYear, report_month__gte=awardMonth)
        qs2 = dates.all().filter(report_year=deadlineYear, report_month__lte=deadlineMonth)
        qs3 = dates.all().filter(report_year__gt=awardYear, report_year__lt=deadlineYear)
        van_max = qs3.union(qs1, qs2)
        van_max_list = list(van_max.values('id', 'vanpool_groups_in_operation'))
        max_value = 0
        max_id = 0
        for i in van_max_list:
            if i['vanpool_groups_in_operation'] > max_value:
                max_value = i['vanpool_groups_in_operation']
                max_id = i['id']
            elif i['vanpool_groups_in_operation'] == max_value:
                if i['id'] > max_id:
                    max_id = i['id']
        van_maximum = vanpool_report.objects.get(id= max_id)
        max_van_date = datetime.date(van_maximum.report_year, van_maximum.report_month, 1)
        #TODO pull vanpool groups in operation and date out of here, input them into the db
        vanpool_expansion_analysis.objects.filter(id=van['id']).update(max_vanpool_date=max_van_date, max_vanpool_numbers = van_maximum.vanpool_groups_in_operation)



def calculate_if_goal_has_been_reached():
    vanExpansion = vanpool_expansion_analysis.objects.order_by('organization_id').values('id', 'expansion_goal', 'organization_id', 'date_of_award', 'deadline')
    for org in vanExpansion:
        awardMonth = org['date_of_award'].month
        awardYear = org['date_of_award'].year
        deadlineYear = org['deadline'].year
        deadlineMonth = org['deadline'].month
        goal = org['expansion_goal']
        orgId = org['organization_id']
        dates = vanpool_report.objects.filter(organization_id =orgId,
                   report_month__isnull=False, vanpool_groups_in_operation__gte=goal, report_year__range = [awardYear, deadlineYear]).values('id','report_year', 'report_month',
                    'vanpool_groups_in_operation', 'organization_id')
        qs1 = dates.all().filter(report_year=awardYear, report_month__gte=awardMonth)
        qs2 = dates.all().filter(report_year=deadlineYear, report_month__lte=deadlineMonth)
        qs3 = dates.all().filter(report_year__gt=awardYear, report_year__lt=deadlineYear)
        goalMet = qs3.union(qs1, qs2)
        if goalMet.exists():
            vanpool_expansion_analysis.objects.filter(id = org['id']).update(vanpool_goal_met = True)


def calculate_remaining_months():
    expansionDeadlines = vanpool_expansion_analysis.objects.values('deadline', 'id').order_by('organization_id')
    for vea in expansionDeadlines:
        deadline = vea['deadline']
        remainder = relativedelta(deadline, datetime.date.today())
        remainingMonths = remainder.months
        if remainingMonths < 0:
            vanpool_expansion_analysis.objects.filter(id = vea['id']).update(expired = True)
            vanpool_expansion_analysis.objects.filter(id=vea['id']).update(months_remaining='Expired')
        else:
            vanpool_expansion_analysis.objects.filter(id=vea['id']).update(months_remaining= '{} months'.format(remainingMonths))


def get_latest_report():
    vanpool_report.objects.all()



def monthdelta(date, delta):
    """
    function to calculate date - delta months
    :param date: a datetime.date object
    :param delta: an int representing the number of months
    :return: a new datetime.date object
    """
    delta = -int(delta)
    m, y = (date.month + delta) % 12, date.year + (date.month + delta - 1) // 12
    if not m: m = 12
    d = min(date.day, [31,
                       29 if y % 4 == 0 and not y % 400 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][
        m - 1])
    return date.replace(day=d, month=m, year=y)


#
def get_wsdot_color(i, hex_or_rgb="hex", alpha=99):
    """
    function to generate and incremented WSDOT color scheme primarily for charts.  If alpha is provided it will return a hex color with an alpha component
    :param i: int
    :param alpha: int
    :param hex_or_rgb: str either 'hex' or 'rgb' selects the output format
    :return: a string representing a WSDOT hex color
    """
    j = i % 8
    if hex_or_rgb == 'hex':
        wsdot_colors = ["#2C8470",
                        "#97d700",
                        "#00aec7",
                        "#5F615E",
                        "#00b140",
                        "#007fa3",
                        "#ABC785",
                        "#593160"]
        color = wsdot_colors[j]
        # HEX with alpha is not compatible with chart js.

    elif hex_or_rgb == 'rgb':
        if alpha == 100:
            alpha = 99
        wsdot_colors = ["rgba(44,132,112,0.{})".format(alpha),
                        "rgba(151,215,0,0.{})".format(alpha),
                        "rgba(0,174,199,0.{})".format(alpha),
                        "rgba(95,97,94,0.{})".format(alpha),
                        "rgba(0,177,64,0.{})".format(alpha),
                        "rgba(0,127,163,0.{})".format(alpha),
                        "rgba(171,199,133,0.{})".format(alpha),
                        "rgba(89,49,96,0.{})".format(alpha)]
        color = wsdot_colors[j]
    return color

def calculate_biennium(date):
    """
    calculates the biennium that the provided data is in
    :param date: a datetime.date object
    :return: str - last two digits of the start year followed by a '-' and then the last two digits of the end year
    """
    import datetime

    if not isinstance(date, datetime.date):
        raise TypeError("date must be a datetime.date object")

    def biennium_str(first_year):
        return str(first_year)[-2:] + "-" + str(first_year + 2)[-2:]

    reference_biennium_start_year = 2017
    if (date.year - reference_biennium_start_year) % 2 == 0:
        start_year = reference_biennium_start_year + (date.year - reference_biennium_start_year)
        if date > datetime.date(start_year, 6, 1):
            return biennium_str(start_year)
        else:
            return biennium_str(start_year - 2)
    else:
        start_year = reference_biennium_start_year + (date.year - reference_biennium_start_year) - 1
        return biennium_str(start_year)

def green_house_gas_per_vanpool_mile():
    """
    Function returns a multiplier to be multiplied with a number of miles traveled by vanpool to yield total CO2 equivalents emited
    :return: vanpool emissions factor
    """
    percent_small_van = 0.60  # update using report found here:G:\Evaluation Group\RVCT and WSRO Vanpool\Info For Greenhouse Gas Calculations\VanpoolSeatingCapcityReport.xlsx (right click on the pivot table and hit refresh to get latest data)
    small_van_mpg = 24.00  # Small Vans are vans with a wheelbase less than 121 inches.  Some but not all 8 passanger vanpool vans have a wheelbase less than 21 inches.  Use the percent of vanpool vans with a passanger capacity of 8 or less.
    large_van_mpg = 17.40
    co2e_per_gallon = 0.00889  # units = transit_metric tones

    fleet_fuel_efficiency = (small_van_mpg * percent_small_van) + (large_van_mpg * (1 - percent_small_van))
    co2_per_vanpool_mile_traveled = (1 / fleet_fuel_efficiency) * co2e_per_gallon

    return co2_per_vanpool_mile_traveled

def green_house_gas_per_sov_mile():
    """
    Function returns a multiplier to be multiplied with a number of miles traveled by vanpool to yield total CO2 equivalents emited
    :return: vanpool emissions factor
    """

    sov_miles_per_gallon = 22
    co2e_per_gallon = 0.00889  # units = transit_metric tones

    co2_per_sov_mile_traveled = (1 / sov_miles_per_gallon) * co2e_per_gallon
    return co2_per_sov_mile_traveled


def get_vanpool_summary_charts_and_table(include_years,
                                         is_org_summary=True,
                                         org_id=None,
                                         include_regions=None,
                                         include_agency_classifications=None):
    """
    This function is used to generate the summary charts and summary table for the vanpool state wide and organization
    summary pages
    :param include_years: int how many years to include in the charts and tables
    :param is_org_summary: bool is it the organization summary or the statewide summary
    :param org_id: int required if is_org_summary is true
    :param include_regions: str required if is_org summary is false
    :param include_agency_classifications:  str required if is_org summary is false
    :return: x_axis_labels, all_charts, summary_table_data, summary_table_data_total
    """

    MEASURES = [
        ("vanpool_miles_traveled", "vanshare_miles_traveled"),
        ("vanpool_passenger_trips", "vanshare_passenger_trips"),
        ("vanpool_groups_in_operation", "vanshare_groups_in_operation"),
    ]

    sov_miles_per_gallon = 22
    co2e_per_gallon = 0.00889  # units = transit_metric tones
    co2_per_sov_mile_traveled = (1 / sov_miles_per_gallon) * co2e_per_gallon

    all_chart_data = [report for report in
                      vanpool_report.objects.order_by('report_year', 'report_month').all() if
                      report.report_year >= datetime.datetime.today().year - include_years]
    x_axis_labels = [report.report_month for report in all_chart_data]
    x_axis_labels = list(dict.fromkeys(x_axis_labels))
    x_axis_labels = list(map(lambda x: calendar.month_name[x], x_axis_labels))

    if not is_org_summary:
        if include_regions != "Statewide":
            if include_regions == "Puget Sound":
                orgs_to_include = organization.objects.filter(classification__in=include_agency_classifications).filter(
                    in_puget_sound_area=True).values_list('id')
            else:
                orgs_to_include = organization.objects.filter(classification__in=include_agency_classifications).filter(
                    in_puget_sound_area=False).values_list('id')
        else:
            orgs_to_include = organization.objects.filter(classification__in=include_agency_classifications).values_list(
                'id')
    else:
        orgs_to_include = [org_id]

    years = range(datetime.datetime.today().year - include_years + 1, datetime.datetime.today().year + 1)

    all_data = vanpool_report.objects.filter(report_year__gte=datetime.datetime.today().year - (include_years - 1),
                                             report_year__lte=datetime.datetime.today().year,
                                             organization_id__in=orgs_to_include).order_by('report_year',
                                                                                           'report_month').all()
    # TODO once the final data is in we need to confirm that the greenhouse gas calculations are correct
    summary_table_data = vanpool_report.objects.filter(
        report_year__gte=datetime.datetime.today().year - (include_years - 1),
        report_year__lte=datetime.datetime.today().year,
        organization_id__in=orgs_to_include,
        report_date__isnull=False,
        vanpool_passenger_trips__isnull=False).values('report_year').annotate(
        table_total_miles_traveled=Sum(F(MEASURES[0][0]) + F(MEASURES[0][1])),
        table_total_passenger_trips=Sum(F(MEASURES[1][0]) + F(MEASURES[2][1])),
        table_total_groups_in_operation=Sum(F(MEASURES[2][0]) + F(MEASURES[2][1])) / Count('report_month',
                                                                                           distinct=True),
        statewide_average_riders_per_van=ExpressionWrapper(Avg(F('average_riders_per_van')) * Sum(F('vanpool_groups_in_operation')+ F('vanshare_groups_in_operation')) /
                                         Sum(F('vanpool_groups_in_operation') + F('vanshare_groups_in_operation')), output_field=FloatField())


    )
    for year in summary_table_data:
        total_sov_co2 = year['table_total_miles_traveled'] * year['statewide_average_riders_per_van']* green_house_gas_per_sov_mile()
        total_van_co2 = year['table_total_miles_traveled'] * green_house_gas_per_vanpool_mile()
        total_co2_saved = total_sov_co2 - total_van_co2
        year['total_co2_saved'] = total_co2_saved
    # TODO once the final data is in we need to confirm that the greenhouse gas calculations are correct
    summary_table_data_total = vanpool_report.objects.filter(
        report_year__gte=datetime.datetime.today().year - (include_years - 1),
        report_year__lte=datetime.datetime.today().year,
        organization_id__in=orgs_to_include).aggregate(
        table_total_miles_traveled=Sum(F(MEASURES[0][0]) + F(MEASURES[0][1])),
        table_total_passenger_trips=Sum(F(MEASURES[1][0]) + F(MEASURES[2][1])),
        statewide_average_riders_per_van=ExpressionWrapper(Avg(F('average_riders_per_van')) * Sum(F('vanpool_groups_in_operation')+ F('vanshare_groups_in_operation')) /
                                         Sum(F('vanpool_groups_in_operation') + F('vanshare_groups_in_operation')), output_field=FloatField())
    )
    total_sov_co2 = summary_table_data_total['table_total_miles_traveled'] * summary_table_data_total['statewide_average_riders_per_van'] * green_house_gas_per_sov_mile()
    total_van_co2 = summary_table_data_total['table_total_miles_traveled'] * green_house_gas_per_vanpool_mile()
    total_co2_saved = total_sov_co2 - total_van_co2
    summary_table_data_total['total_co2_saved'] = total_co2_saved

    all_charts = list()
    for i in range(len(MEASURES) + 1):
        # to include green house gasses
        if i == len(MEASURES):
            all_chart_data = all_data.values('report_year', 'report_month').annotate(
                result=Sum((F(MEASURES[0][0]) + F(MEASURES[0][1])) * (
                            F('average_riders_per_van') - 1)) * green_house_gas_per_sov_mile() - Sum(
                    F(MEASURES[0][0]) + F(MEASURES[0][1])) * green_house_gas_per_vanpool_mile()
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

    return x_axis_labels, all_charts, summary_table_data, summary_table_data_total


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

def yearchange(user_org_id, start_year, end_year, measure):

    start_vanpool_report_year = vanpool_report.objects. \
        filter(organization_id=user_org_id, report_date__isnull=False, report_month=12, report_year=start_year).first()
    end_vanpool_report_year = vanpool_report.objects. \
        filter(organization_id=user_org_id, report_date__isnull=False, report_month=12, report_year=end_year).first()

    def overall_change(measure):
        """Return a list where first item is the current months stat and the second item is the year over year grouwth"""
        start_measure_value = getattr(start_vanpool_report_year, measure)
        end_measure_value = getattr(end_vanpool_report_year, measure)
        if start_measure_value is None:
            overall_growth = "NA"
        else:
            overall_growth = (end_measure_value/start_measure_value) - 1
            overall_growth = round(overall_growth*100, 0)

        return [end_measure_value, overall_growth]

    return [measure, overall_change(measure)]


# TODO make this real
def get_current_summary_report_year():
    return 2019


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def get_all_cover_sheet_steps_completed(organization_id):
    organization_progress, created = summary_organization_progress.objects.get_or_create(organization_id=organization_id)
    result = organization_progress.started and \
             organization_progress.address_and_organization and \
             organization_progress.organization_details and \
             organization_progress.service_cover_sheet

    return result


def get_url_for_first_missed_step(organization_id):
    organization_progress, created = summary_organization_progress.objects.get_or_create(organization_id=organization_id)
    if created:
        pass
    pass


def get_cover_sheet_submitted(organization_id):
    return summary_report_status.objects.get(year=get_current_summary_report_year(), organization_id=organization_id).cover_sheet_submitted_for_review


def get_all_data_steps_completed(organization_id):
    organization_progress, created = summary_organization_progress.objects.get_or_create(organization_id=organization_id)
    result = organization_progress.confirm_service and \
             organization_progress.transit_data and \
             organization_progress.revenue and \
             organization_progress.expenses and \
             organization_progress.ending_balances

    return result

def get_data_submitted(organization_id):
    return summary_report_status.objects.get(year=get_current_summary_report_year(),
                                             organization_id=organization_id).data_report_submitted_for_review

@transaction.atomic
def reset_summary_reporter_tracking(year):
    year_reports = summary_report_status.objects.filter(year=year)
    for item in year_reports:
        item.cover_sheet_status = "With user"
        item.cover_sheet_submitted_for_review = False
        item.data_report_status = "With user"
        item.data_report_submitted_for_review = False
        item.save()


@transaction.atomic
def reset_all_orgs_summary_progress():
    for item in summary_organization_progress.objects.all():
        item.delete()

