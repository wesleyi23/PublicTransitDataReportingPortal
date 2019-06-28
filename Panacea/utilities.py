from .models import organization, vanpool_expansion_analysis, vanpool_report
from django.db.models import Max, Subquery, F, OuterRef
import datetime
from dateutil.relativedelta import relativedelta
#####
# Utility functions
#####

#

def find_organizations_name(organizationIds):
    organization_names = organization.objects.filter(id__in=organizationIds).values('name').order_by('organization_id')
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
        vp = vanpool_report.objects.all()
        pv = vp.filter(organization_id =orgId,
                   report_month__isnull=False,
                   vanpool_groups_in_operation__isnull=False, report_year__gte=awardYear,
                                            report_month__gte=awardMonth, report_year__lte=deadlineYear,
                                            report_month__lte=deadlineMonth).order_by('-id').values('id')
        latest_vanpool = vp.annotate(latest=Subquery(pv[:1])).filter(id=F('latest')).values('report_year', 'report_month',
                                                                                        'vanpool_groups_in_operation',
                                                                                        'organization_id').order_by('organization_id')
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

        van_max = vanpool_report.objects.filter(organization_id =orgId, report_year__gte=awardYear,
                                            report_month__gte=awardMonth, report_year__lte=deadlineYear,
                                            report_month__lte=deadlineMonth).values('report_year', 'report_month','vanpool_groups_in_operation').annotate(max_van=Max('vanpool_groups_in_operation')).order_by('organization_id')
        if len(van_max) > 1:
            van_max = van_max.latest('id')
            vanMaxList.append(van_max)
        else:
            vanMaxList.append(van_max)
    return vanMaxList


def calculate_if_goal_has_been_reached():
    awardDate = vanpool_expansion_analysis.objects.values('date_of_award').order_by('organization_id')
    awardDate = awardDate[0]
    awardMonth = awardDate.month
    awardYear = awardDate.year
    deadlineDate = vanpool_expansion_analysis.objects.values('deadline').order_by('organization_id')
    deadlineDate = deadlineDate[0]
    deadlineMonth = deadlineDate.month
    deadlineYear = deadlineDate.year
    vanExpansion = vanpool_expansion_analysis.objects.order_by('organization_id').values('id', 'expansion_goal', 'organization_id')
    expansionGoalList = []
    for org in vanExpansion:
        award_month = org['date_of_award'].month
        award_year = org['date_of_award'].year
        goal = org['expansion_goal']
        org_id = org['organization_id']
        goalMet = vanpool_report.objects.filter(organization_id=org_id, report_year__gte=award_year,
                                             report_month__gte=award_month,
                                             vanpool_groups_in_operation__gte=goal, report_month__lte=deadlineMonth, report_year_lte=deadlineYear).values('id', 'report_year',
                                                                                           'report_month','vanpool_groups_in_operation','organization_id')
        if goalMet.exists():
            expansionGoalList.append(goalMet.earliest('id'))
            vanpool_expansion_analysis.objects.get(id = org['id']).update(vanpool_goal_met = True)
        else:
            expansionGoalList.append('')
    return expansionGoalList


def calculate_remaining_months():
    remainingMonthsList = []
    expansionDeadlines = vanpool_expansion_analysis.objects.values('deadline', 'id').order_by('organization_id')
    for vea in expansionDeadlines:
        deadline = vea['deadline']
        remainder = relativedelta(deadline, datetime.date.today())
        remainingMonths = remainder.months
        if remainingMonths < 0:
            vanpool_expansion_analysis.objects.get(id = vea['id']).update(expired = True)
            remainingMonthsList.append('Deadline Expired')
        else:
            remainingMonthsList.append(remainingMonths)
    return remainingMonths




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


