import calendar
import json
from .models import organization, vanpool_expansion_analysis, vanpool_report
from django.db.models import Max, Subquery, F, OuterRef, Case, CharField, Value, When, Sum, Count

import datetime
from dateutil.relativedelta import relativedelta
#####
# Utility functions
#####

#



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
    co2e_per_gallon = 0.008887  # units = metric tones

    fleet_fuel_efficiency = (small_van_mpg * percent_small_van) + (large_van_mpg * (1 - percent_small_van))
    co2_per_vanpool_mile_traveled = (1 / fleet_fuel_efficiency) * co2e_per_gallon

    return co2_per_vanpool_mile_traveled

def green_house_gas_per_sov_mile():
    """
    Function returns a multiplier to be multiplied with a number of miles traveled by vanpool to yield total CO2 equivalents emited
    :return: vanpool emissions factor
    """

    sov_miles_per_gallon = 22
    co2e_per_gallon = 0.008887  # units = metric tones

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
        green_house_gas_prevented=Sum((F(MEASURES[0][0]) + F(MEASURES[0][1])) * (
                    F('average_riders_per_van') - 1)) * green_house_gas_per_sov_mile() - Sum(
            F(MEASURES[0][0]) + F(MEASURES[0][1])) * green_house_gas_per_vanpool_mile()
    )

    # TODO once the final data is in we need to confirm that the greenhouse gas calculations are correct
    summary_table_data_total = vanpool_report.objects.filter(
        report_year__gte=datetime.datetime.today().year - (include_years - 1),
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
