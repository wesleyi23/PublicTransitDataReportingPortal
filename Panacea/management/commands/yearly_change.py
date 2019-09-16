from django.core.management.base import BaseCommand
from Panacea.models import vanpool_report


# #KI VERSION 2

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

        return [end_measure_value, overall_growth]

    return [measure, overall_change(measure)]


class Command(BaseCommand):
    help = 'Creates change from given year'

    def add_arguments(self, parser):
        parser.add_argument('user_org_id', type=int)
        parser.add_argument('start_year', type=int)
        parser.add_argument('end_year', type=int)
        parser.add_argument('measure', type=str)

    def handle(self, *args, **options):
        print(yearchange(options['user_org_id'],
              options['start_year'],
              options['end_year'],
              options['measure']))
