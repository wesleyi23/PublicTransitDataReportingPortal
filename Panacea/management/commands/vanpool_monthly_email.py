from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.management.base import BaseCommand
from django.conf import settings
from django.template.loader import render_to_string
from Panacea.models import organization, profile, custom_user, vanpool_report
from datetime import datetime, timedelta


def select_vanpool_organizations_by_email_type(email_type):
    '''
    This function returns organizations with a vanpool program based on the email they should receive depending on how
    late they are in reporting.
    :param email_type: the type of email the organization should receive
    :return: organizations object
    '''

    if email_type == 'reminder':
        target_date = datetime.today() - timedelta(days=45)
    elif email_type == 'past due':
        target_date = datetime.today() - timedelta(days=75)
    elif email_type == 'final warning':
        target_date = datetime.today() - timedelta(days=105)

    org_ids = vanpool_report.objects.filter(report_date__gte=target_date).values_list('organization_id',
                                                                                      flat=True).distinct()

    vanpool_organizations = organization.objects.filter(vanpool_program=True,
                                                        id__in=org_ids)
    return vanpool_organizations


def select_vanpool_users(organizations):
    '''
    This function returns users that have the vanpool group permissions and are in the organization provided
    :param organizations: organizations model objects - most often pulled from select_vanpool_organizations()
    :return: returns custom user objects
    '''
    user_ids = profile.objects.filter(organization__in=organizations).values_list('custom_user_id',
                                                                                  flat=True).distinct()


    vanpool_users = custom_user.objects.filter(id__in=user_ids,
                                               groups__name='Vanpool reporter')

    return vanpool_users


def send_vanpool_reminder_emails(recipient_list, email_type):
    '''
    This function sends vanpool reminder emails
    :param recipient_list: List of email address to send
    :param email_type: the type of email to send valid options are ['reminder', 'past due', 'final warning']
    :return: Sends emails
    '''

    # if settings.SEND_EMAILS == False:
    #     recipient_list = [settings.DEFAULT_FROM_EMAIL, 'wesleyi@wsdot.wa.gov']

    if email_type == 'reminder':
        template_file = 'reminder'
        subject = 'Vanpool report reminder'
    elif email_type == 'past due':
        template_file = 'past_due'
        subject = 'Vanpool past due'
    elif email_type == 'final warning':
        template_file = 'final_warning'
        subject = 'Vanpool 3 months past due'

    html_message = render_to_string('emails/vanpool_email/' + template_file + '.html', {})
    msg_plain = render_to_string('emails/vanpool_email/' + template_file + '.txt', {})

    for recipient in recipient_list:
        send_mail(
            subject=subject,
            message=msg_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
        )


class Command(BaseCommand):
    def add_arguments(self, parser):

        parser.add_argument(
            '--test',
            action='store_true',
            help='Sends test email.',
        )

    def handle(self, *args, **options):
        if options['test']:
            recipient_list = settings.ADMIN_EMAILS
            for email_type in ['reminder', 'past due', 'final warning']:
                send_vanpool_reminder_emails(recipient_list, email_type)

        else:
            for email_type in ['reminder', 'past due', 'final warning']:
                vanpool_organizations = select_vanpool_organizations_by_email_type(email_type)
                recipient_list = select_vanpool_users(vanpool_organizations)
                recipient_list = recipient_list.values_list("email", flat=True)
                print(recipient_list)
                send_vanpool_reminder_emails(recipient_list, email_type)


