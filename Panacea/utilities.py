from .models import organization, vanpool_expansion_analysis, vanpool_report
from django.db.models import Max, Subquery, F, OuterRef, Case, CharField, Value, When

import datetime
from dateutil.relativedelta import relativedelta
#####
# Utility functions
#####

#

def find_organizations_name():
    veaOrgs = vanpool_expansion_analysis.objects.values('organization_id').distinct()
    for i in veaOrgs:
        orgId = i['organization_id']
        orgName = organization.objects.get(id = orgId)
        orgName = str(orgName)
        vanpool_expansion_analysis.objects.filter(organization_id=orgId).update(organization_name = orgName)


def calculate_latest_vanpool():
    latestVanData = vanpool_expansion_analysis.objects.values('id', 'date_of_award', 'deadline', 'organization_id').order_by('organization_id')
    for van in latestVanData:
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

def calculate_biennium(date):
    import datetime

    if not isinstance(date, datetime.date):
        raise TypeError("date must be a datetime.date object")

    def biennium_str(first_year):
        return str(first_year)[-2:]+ "-" + str(first_year + 2)[-2:]

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

