from celery.task import task
from django.core.mail import send_mail
from celery.task import periodic_task
from celery import shared_task, task
from celery.schedules import crontab
from Panacea.models import custom_user, organization, vanpool_report, profile
import datetime
from dateutil import relativedelta
from TransitData import settings
from django.template.loader import render_to_string
from mailer.engine import send_all

#@periodic_task(run_every = crontab(minute = 2))
#def email_tasks():
 #   send_all()

#@shared_task()
#def send_emails_now():
 #   send_mail('Late Vanpool Reporting Notice', 'It is an automated email', settings.EMAIL_HOST_USER, ['wesleyi@wsdot.wa.gov'], fail_silently=False)


@periodic_task(run_every = crontab(hour=7, minute=30, day_of_week= 'monday'), name = "week_late", ignore_result = True)
def week_late():
    for i in organization.objects.filter(vanpool_program=True):
        bad_orgs = ['Washington State Department of Transportation', 'Test Reporter', 'Test Reporter 2']
        # need to add an active/inactive to orgs, so we aren't spamming random people
        if i.name in bad_orgs:
            continue
        else:
            van_rep = vanpool_report.objects.filter(vanpool_groups_in_operation__isnull=False,
                                                    organization_id=i.id).latest('id')
            if van_rep.report_month == 12:
                nextMonth = 1
                reportYear = van_rep.report_year + 1
            else:
                nextMonth = van_rep.report_month + 1
                reportYear = van_rep.report_year
            latest_report = datetime.date(reportYear, nextMonth, 1)
            due_date = latest_report + relativedelta(months=1)
            users = profile.objects.filter(organization_id=i.id).values('custom_user_id')
            user_list = custom_user.objects.filter(id__in=users, is_active=True).values('first_name', 'last_name',
                                                                                        'email')
            user_list = list(user_list)
            for user in user_list:
                if datetime.date.today() >= due_date + relativedelta(days=7):
                    msg_plain = render_to_string('emails/past_due_email.txt', {'firstname': user['first_name'], 'lastname': user['last_name'], 'org': i.name, 'due_date': due_date})
                    msg_html = render_to_string('emails/past_due_email.html', {'firstname': user['first_name'], 'lastname': user['last_name'], 'org': i.name, 'due_date': due_date})
                    send_mail('Late Vanpool Reporting Notice', msg_plain, settings.EMAIL_HOST_USER,
                              [user['email']], html_message=msg_html, fail_silently=False)



@periodic_task(run_every = crontab(minute = 0, hour = 8), name = "check_due_date_of_report", ignore_result = True )
def check_due_date_of_report():
    for i in organization.objects.filter(vanpool_program = True):
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
                    msg_plain = render_to_string('emails/past_due_email.txt',
                                                 {'firstname': user['first_name'], 'lastname': user['last_name'],
                                                  'org': i.name, 'due_date': due_date})
                    msg_html = render_to_string('emails/past_due_email.html',
                                                {'firstname': user['first_name'], 'lastname': user['last_name'],
                                                 'org': i.name, 'due_date': due_date})
                    send_mail('Vanpool Reporting Reminder', msg_plain, settings.EMAIL_HOST_USER,[user['email']], html_message=msg_html, fail_silently=False)
                elif datetime.date.today() == due_date:
                   msg_plain = render_to_string('emails/past_due_email.txt',
                                                {'firstname': user['first_name'], 'lastname': user['last_name'],'org': i.name, 'due_date': due_date})
                   msg_html = render_to_string('emails/past_due_email.html',
                                               {'firstname': user['first_name'], 'lastname': user['last_name'],'org': i.name, 'due_date': due_date})
                   send_mail('Vanpool Reporting Due Today', msg_plain, settings.EMAIL_HOST_USER,[user['email']], html_message=msg_html, fail_silently=False)

                elif datetime.date.today() == due_date + relativedelta(days=1):
                    msg_plain = render_to_string('emails/past_due_email.txt',
                                                 {'firstname': user['first_name'], 'lastname': user['last_name'],
                                                  'org': i.name, 'due_date': due_date})
                    msg_html = render_to_string('emails/past_due_email.html',
                                                {'firstname': user['first_name'], 'lastname': user['last_name'],
                                                 'org': i.name, 'due_date': due_date})
                    send_mail('Vanpool Reporting Past Due', msg_plain, settings.EMAIL_HOST_USER,
                              [user['email']], html_message=msg_html, fail_silently=False)

                elif datetime.date.today() == due_date + relativedelta(days=2):
                    msg_plain = render_to_string('emails/past_due_email.txt',
                                                 {'firstname': user['first_name'], 'lastname': user['last_name'],
                                                  'org': i.name, 'due_date': due_date})
                    msg_html = render_to_string('emails/past_due_email.html',
                                                {'firstname': user['first_name'], 'lastname': user['last_name'],
                                                 'org': i.name, 'due_date': due_date})
                    send_mail('Vanpool Reporting Past Due', msg_plain, settings.EMAIL_HOST_USER,
                              [user['email']], html_message=msg_html, fail_silently=False)

                else:
                    pass
