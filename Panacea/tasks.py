from celery.task import task
from django.core.mail import send_mail
from celery.task import periodic_task
from celery.schedules import crontab
from .models import custom_user, organization, vanpool_report, profile
import datetime
from dateutil import relativedelta


@periodic_task(run_every = crontab(minute=0, hour=7, day_of_month="mon"), name = "week_late", ignore_result = True)
def week_late():
    for i in organization.objects.all():
        bad_orgs = ['Washington State Department of Transportation', 'Test Reporter', 'Test Reporter 2']
        # need to add an active/inactive to orgs, so we aren't spamming random people
        if i.name in bad_orgs:
            continue
        else:
            van_rep = vanpool_report.objects.filter(organization_id=i.id).latest('id')
            latest_report = datetime.date(van_rep.report_year, van_rep.report_month, van_rep.report_date)
            due_date = latest_report + relativedelta(months=1)
            users = profile.objects.filter(organization_id=i.id).values('custom_user_id')
            user_list = custom_user.objects.filter(id__in=users, is_active=True).values('first_name', 'last_name','email')
            for user in user_list:
                if datetime.date.today() >= due_date + relativedelta(days=7):
                    past_due_email = '''Dear {} {},
                                        This is to remind you that your most recent vanpool data for {} was due on {}. Please login to the
                                        vanpool portal at your earliest convenience and report your data. If you have any questions about reporting,
                                        please direct them to x'''.format(user['first_name'], user['last_name'], i.name, due_date)
                    send_mail('Late Vanpool Reporting Notice', past_due_email, 'webmaster@watransitdata.wa.gov', [user['email']], fail_silently=False)
                else:
                    pass



@periodic_task(run_every = crontab(minute = 0, hour = 8), name = "check_due_date_of_report", ignore_result = True )
def check_due_date_of_report():
    for i in organization.objects.all():
        bad_orgs = ['Washington State Department of Transportation', 'Test Reporter', 'Test Reporter 2']
        # need to add an active/inactive to orgs, so we aren't spamming random people
        if i.name in bad_orgs:
            continue
        else:
            van_rep = vanpool_report.objects.filter(organization_id=i.id).latest('id')
            latest_report = datetime.date(van_rep.report_year, van_rep.report_month, van_rep.report_date)
            due_date = latest_report + relativedelta(months=1)
            users = profile.objects.filter(organization_id=i.id).values('custom_user_id')
            user_list = custom_user.objects.filter(id__in=users, is_active=True).values('first_name', 'last_name','email')
            for user in user_list:
                if datetime.date.today() == due_date - relativedelta(days=5):
                    early_notice_email = '''Dear {} {},
                                    This is to remind you that your most recent vanpool data for {} is due {}. Please login to the
                                    vanpool portal at your earliest convenience and report your data. If you have any questions about reporting,
                                    please direct them to x'''.format(user['first_name'], user['last_name'], i.name, due_date)
                    send_mail('Vanpool Reporting Reminder', early_notice_email, 'webmaster@watransitdata.wa.gov', [user['email']], fail_silently=False)
                elif datetime.date.today() == due_date:
                   due_today_email = '''Dear {} {},
                                    This is to remind you that your most recent vanpool data for {} is due today. Please login to the
                                    vanpool portal at your earliest convenience and report your data. If you have any questions about reporting,
                                    please direct them to x'''.format(user['first_name'], user['last_name'], i.name)
                   send_mail('Vanpool Reporting Reminder', due_today_email, 'webmaster@watransitdata.wa.gov',
                              [user['email']], fail_silently=False)
                elif datetime.date.today() == due_date + relativedelta(days=1):
                    past_due_email = '''Dear {} {},
                                     This is to remind you that your most recent vanpool data for {} was due on {}. Please login to the
                                     vanpool portal at your earliest convenience and report your data. If you have any questions about reporting,
                                     please direct them to x'''.format(user['first_name'], user['last_name'], i.name, due_date)
                    send_mail('Vanpool Reporting is Past Due', past_due_email, 'webmaster@watransitdata.wa.gov', [user['email']], fail_silently=False)

                elif datetime.date.today() == due_date + relativedelta(days=2):
                    past_due_email = '''Dear {} {},
                                     This is to remind you that your most recent vanpool data for {} was due on {}. Please login to the
                                     vanpool portal at your earliest convenience and report your data. If you have any questions about reporting,
                                     please direct them to x'''.format(user['first_name'], user['last_name'], i.name, due_date)
                    send_mail('Vanpool Reporting is Past Due', past_due_email, 'webmaster@watransitdata.wa.gov',
                              [user['email']], fail_silently=False)

                else:
                    pass
