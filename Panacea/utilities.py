from .models import organization, vanpool_expansion_analysis, vanpool_report
from django.db.models import Max, Subquery, F, OuterRef, Case, CharField, Value, When

import datetime
from dateutil.relativedelta import relativedelta
#####
# Utility functions
#####

#

def find_organizations_name(organizationIds):
    organization_names = []
    for i in organizationIds:
        orgname = organization.objects.get(id = i['organization_id'])
        organization_names.append(orgname)
    return organization_names

def calculate_latest_vanpool():
    latestVanpoolList = []
    latestVanData = vanpool_expansion_analysis.objects.values('date_of_award', 'deadline', 'organization_id').order_by('organization_id')
    for van in latestVanData:
        awardMonth = van['date_of_award'].month
        awardYear = van['date_of_award'].year
        deadlineYear = van['deadline'].year
        deadlineMonth = van['deadline'].month
        orgId = van['organization_id']

        dates = vanpool_report.objects.filter(organization_id =orgId,
                   report_month__isnull=False, vanpool_groups_in_operation__gte=0, report_year__gte = awardYear, report_year__lte = deadlineYear).values('id','report_year', 'report_month',
                    'vanpool_groups_in_operation', 'organization_id')
        qs1 = dates.all().filter(report_year = awardYear, report_month__gte = awardMonth)
        qs2 = dates.all().filter(report_year = deadlineYear, report_month__lte = deadlineMonth)
        qs3 = dates.all().filter(report_year__gt = awardYear, report_year__lt = deadlineYear)
        latest_vanpool = qs3.union(qs1, qs2)
        if len(latest_vanpool) > 1:
            latest_vanpool = latest_vanpool.latest('id')
            latestVanpoolList.append(latest_vanpool)
        else:
            latestVanpoolList.append(latest_vanpool)
    return latestVanpoolList


def find_maximum_vanpool(organizationIds):
    vanMaxList = []
    vanMaxData = vanpool_expansion_analysis.objects.values('date_of_award', 'deadline', 'organization_id').order_by('organization_id')
    for van in vanMaxData:
        awardMonth = van['date_of_award'].month
        awardYear = van['date_of_award'].year
        deadlineYear = van['deadline'].year
        deadlineMonth = van['deadline'].month
        orgId = van['organization_id']
        dates = vanpool_report.objects.filter(organization_id=orgId,
                                              report_month__isnull=False, vanpool_groups_in_operation__gte=0,
                                              report_year__gte=awardYear, report_year__lte=deadlineYear).values('vanpool_groups_in_operation', 'report_year', 'report_month', 'id')
        qs1 = dates.all().filter(report_year=awardYear, report_month__gte=awardMonth)
        qs2 = dates.all().filter(report_year=deadlineYear, report_month__lte=deadlineMonth)
        qs3 = dates.all().filter(report_year__gt=awardYear, report_year__lt=deadlineYear)
        van_max = qs3.union(qs1, qs2)
        print(type(van_max[0]['vanpool_groups_in_operation']))


        van_maximum = vanpool_report.objects.filter(id__in = vanMaxIds).annotate(maxvan = Max('vanpool_groups_in_operation'))
        if len(van_maximum) > 1:
            van_maximum = van_maximum.latest('id')
            vanMaxList.append(van_maximum)
        else:
            vanMaxList.append(van_maximum)
    print(len(vanMaxList))
    return vanMaxList


def calculate_if_goal_has_been_reached():
    vanExpansion = vanpool_expansion_analysis.objects.order_by('organization_id').values('id', 'expansion_goal', 'organization_id', 'date_of_award', 'deadline')
    expansionGoalList = []
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
            expansionGoalList.append(goalMet.earliest('id'))
            vanpool_expansion_analysis.objects.filter(id = org['id']).update(vanpool_goal_met = True)
        else:
            expansionGoalList.append('')
    return expansionGoalList


def calculate_remaining_months():
    remainingMonthsList = []
    expansionDeadlines = vanpool_expansion_analysis.objects.values('deadline', 'id').order_by('organization_id')
    print(expansionDeadlines)
    for vea in expansionDeadlines:
        deadline = vea['deadline']
        remainder = relativedelta(deadline, datetime.date.today())
        remainingMonths = remainder.months
        if remainingMonths < 0:
            vanpool_expansion_analysis.objects.filter(id = vea['id']).update(expired = True)
            remainingMonthsList.append('Deadline Expired')
        else:
            remainingMonthsList.append(remainingMonths)
    return remainingMonthsList




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
def get_wsdot_color(i):
    """
    function to generate and incremented WSDOT color scheme primarily for charts
    :param i: int
    :return: a string representing a WSDOT hex color
    """
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


