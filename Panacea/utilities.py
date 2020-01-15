import calendar
import json

from django_pandas.io import read_frame
import pandas as pd
from .models import organization, vanpool_expansion_analysis, vanpool_report, profile, transit_data, service_offered, transit_mode, revenue
from django.db.models import Max, Subquery, F, OuterRef, Case, CharField, Value, When, Sum, Count, Avg, FloatField, \
    ExpressionWrapper
from django.db.models.functions import Coalesce

import datetime
from dateutil.relativedelta import relativedelta
#####
# Utility functions
#####

#

def get_farebox_and_vp_revenues(years, user_org_id):
    farebox = transit_data.objects.filter(organization_id=user_org_id, year__in=years, transit_metric__name='Farebox Revenues',
                                transit_mode_id__in= [1,2,4,5,6,7,8,9,10]).values('year').annotate(reported_value = Sum('reported_value'))
    farebox = read_frame(farebox)
    farebox['revenue_source'] = 'Farebox Revenues'
    vanpool = transit_data.objects.filter(organization_id=user_org_id, year__in=years,
                                          transit_metric__name='Farebox Revenues',
                                          transit_mode_id__in=[3]).values('year').annotate(reported_value=Sum('reported_value'))
    vanpool = read_frame(vanpool)
    vanpool['revenue_source'] = 'Vanpooling Revenue'
    fares = pd.concat([farebox, vanpool], axis=0)
    return fares

def other_operating_sub_total(years, user_org_id):
    other_op = revenue.objects.filter(organization_id=user_org_id, year__in=years, revenue_source__name__in= ['Other-Advertising',
        'Other-Gain (Loss) on Sale of Assets', 'Other-Interest', 'Other-MISC']).values('year').annotate(reported_value = Sum('reported_value'))
    other_op = read_frame(other_op)
    other_op['revenue_source'] = 'Other Operating Sub-Total'
    return other_op

def build_revenue_table(years, user_org_id):
    data_revenue = revenue.objects.filter(organization_id = user_org_id, year__in = years)
    df = read_frame(data_revenue)
    count = 0
    for year in years:
        testdf = df[df.year == year]
        print(testdf.columns)
        testdf = testdf[testdf.reported_value.notna()][['id', 'revenue_source', 'reported_value']]
        testdf['year'] = year
        if count == 0:
            finaldf = testdf
            count += 1
        else:
            finaldf = pd.concat([testdf, finaldf], axis=0)
    fares = get_farebox_and_vp_revenues(years, user_org_id)
    other_op = other_operating_sub_total(years, user_org_id)
    finaldf = pd.concat([finaldf, fares, other_op], axis=0)
    finaldf = finaldf.pivot(index='revenue_source', columns='year', values='reported_value').fillna(0)



def data_prep_for_transits(years, user_org_id):
    '''function for pulling all available data within certain years for a transit and pushing it out to a summary sheet'''
    services_offered = service_offered.objects.filter(organization_id=user_org_id).values('administration_of_mode',
                                                                                          'transit_mode_id')
    data_transit = transit_data.objects.filter(organization_id=user_org_id, year__in=years)
    function_count = 0
    # dual for loops, one for services offered, one for the years in existence
    for i in services_offered:
        filter = data_transit.filter(administration_of_mode=i['administration_of_mode'],
                                     transit_mode_id=i['transit_mode_id'])
        df = read_frame(filter)
        count = 0
        for year in years:
            testdf = df[df.year == year]
            testdf = testdf[testdf.reported_value.notna()][['id', 'transit_metric', 'reported_value']]
            testdf['year'] = year
            if count == 0:
                finaldf = testdf
                count += 1
            else:
                finaldf = pd.concat([testdf, finaldf], axis=0)
                # pivot method here turns transit metics into the index and years into columns
        finaldf = finaldf.pivot(index='transit_metric', columns='year', values='reported_value').fillna(0)
        order_list = ['Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles',
                      'Total Vehicle Miles', 'Passenger Trips',
                      'Diesel Fuel Consumed (gallons)', 'Gasoline Fuel Consumed (gallons)',
                      'Propane Fuel Consumed (gallons)', 'Electricity Consumed (kWh)',
                      'Employees - FTEs', 'Operating Expenses', 'Farebox Revenues']
        # orders the index based on Summary styling
        finaldf = finaldf.reindex(order_list).dropna()
        finaldf = finaldf.reset_index()
        # adds a percent change column
        finaldf['Percentage Change'] = ((finaldf.iloc[:, 3] - finaldf.iloc[:, 2]) / finaldf.iloc[:, 2])* 100
        finaldf['role'] = 'body'
        transit_name = transit_mode.objects.filter(id=i['transit_mode_id']).values('name')[0]['name']
        mode_name = '{} ({})'.format(transit_name, i['administration_of_mode'])
        mode_list = [mode_name, '', '', '', '', 'heading']
        columns_list = finaldf.columns.tolist()
        mode_list_df = pd.DataFrame(dict(zip(columns_list, mode_list)), index = [0])
        finaldf = pd.concat([mode_list_df, finaldf]).reset_index(drop=True)
        if function_count == 0:
            enddf = finaldf
            function_count += 1
        else:
            enddf = pd.concat([enddf, finaldf], axis=0)
    enddf = enddf.fillna('-')
    enddf.columns = ['transit_metric', 'year1', 'year2', 'year3', 'percent_change', 'role']
    return enddf


def complete_data():
    latest_data = vanpool_report.objects.filter(vanpool_groups_in_operation__isnull=False).values('report_year','report_month').annotate(Count('id')).order_by('-id__count', '-report_year', '-report_month').first()
    return latest_data


def calculate_percent_change(data1, data2):
    percent = round((data1 - data2)/data2, 2)
    percent = percent*100
    return percent


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
    print(id)
    user_profile_data = profile.objects.get(custom_user=id)
    org = user_profile_data.organization_id
    return org

def find_user_organization(id):
    user_profile_data = profile.objects.get(custom_user=id)
    print(user_profile_data)
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
    return 2018


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value




