from django.core.management.base import BaseCommand
from Panacea.models import vanpool_report, organization
import datetime
import calendar


def add_months(source_date, months):
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('year', type=int)

    def handle(self, *args, **options):
        num_results = vanpool_report.objects.filter(report_year=options['year']).count()
        print(num_results)
        if num_results < 1:
            for month in vanpool_report.REPORT_MONTH:
                for org in organization.objects.all():
                    new_report = vanpool_report()
                    new_report.report_type_id = 2
                    new_report.report_year = options['year']
                    new_report.report_month = month[0]
                    new_report.report_date = None
                    new_report.organization = org
                    new_report.save(no_report_date=True)


