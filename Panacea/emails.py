from .models import custom_user, profile, cover_sheet, organization
from django.core.mail import send_mail
from TransitData import settings
from django.template.loader import render_to_string


def send_user_registration_email(user_id):
    emailRecipient = custom_user.objects.filter(id = user_id).values('first_name','last_name')
    name = emailRecipient.values_list('first_name', flat=True)
    emailAddress = custom_user.objects.filter(id = user_id).values_list('email', flat = True)
    msg_plain = render_to_string('emails/registration_email.txt', {'firstname':name[0]})
    msg_html = render_to_string('emails/registration_email.html', {'firstname': name[0]})
    send_mail('Welcome to WSDOT\'s Public Transit Data Reporting Portal', msg_plain, settings.DEFAULT_FROM_EMAIL, [emailAddress[0]], html_message=msg_html,)


def active_permissions_request_notification(dev_mode=settings.dev_mode):
    if dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov']
    else:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov']

    msg_html = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
    msg_plain = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
    send_mail(
        subject='Active Permissions Request - Public Transportation Reporting Portal',
        message=msg_plain,
        from_email='permissions@ptreportingportal.gov',
        recipient_list= recipient_list,
        html_message= msg_html, fail_silently=False)


def notify_user_that_permissions_have_been_requested(full_name, groups, email, dev_mode=settings.dev_mode):
    if dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov' ]
    else:
        recipient_list = [email, ]

    msg_html = render_to_string('emails/request_permissions_email.html',
                                {'user_name': full_name, 'groups': groups})
    msg_plain = render_to_string('emails/request_permissions_email.txt',
                                 {'user_name': full_name, 'groups': groups})
    send_mail(
        subject='Active Permissions Request - Public Transportation Reporting Portal',
        message=msg_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=msg_html,
    )


def cover_sheet_returned_to_user(org_id, dev_mode=settings.dev_mode):
    if dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov' ]
    else:
        recipient_list = get_organization_summary_email_address(org_id)

    msg_html = render_to_string('emails/coversheet_returned_to_user.html',
                                {})
    msg_plain = render_to_string('emails/coversheet_returned_to_user.txt',
                                 {})
    send_mail(
        subject='Coversheet Followup - Public Transportation Reporting Portal',
        message=msg_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=msg_html,
    )


def cover_sheet_review_complete(org_id, dev_mode=settings.dev_mode):
    if dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov' ]
    else:
        recipient_list = get_organization_summary_email_address(org_id)

    msg_html = render_to_string('emails/coversheet_review_complete.html',
                                {})
    msg_plain = render_to_string('emails/request_permissions_email.txt',
                                 {})
    send_mail(
        subject='Coversheet Review Completed - Public Transportation Reporting Portal',
        message=msg_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=msg_html,
    )


def data_report_review_complete(org_id, dev_mode=settings.dev_mode):
    if dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov' ]
    else:
        recipient_list = get_organization_summary_email_address(org_id)

    msg_html = render_to_string('emails/data_report_review_complete.html',
                                {})
    msg_plain = render_to_string('emails/data_report_review_complete.txt',
                                 {})
    send_mail(
        subject='Summary Data Report Review Completed - Public Transportation Reporting Portal',
        message=msg_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=msg_html,
    )


def to_wsdot_cover_sheet_submitted(org_id, dev_mode=settings.dev_mode):
    if dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov']
    else:
        recipient_list = get_wsdot_coversheet_reviewer_email()

    org_name = organization.objects.get(id=org_id).name
    subject = org_name + " Submitted Coversheet"

    msg_html = "<!DOCTYPE html><html lang='en'><body><p>" + subject + "</p></body></html>"
    msg_plain = subject

    send_mail(
        subject=subject,
        message=msg_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=msg_html,
    )


def to_wsdot_data_report_submitted(org_id, dev_mode=settings.dev_mode):
    if dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov' ]
    else:
        recipient_list = get_wsdot_data_report_reviewer_email()

    org_name = organization.objects.get(id=org_id).name
    subject = org_name + " Submitted Data Report"

    msg_html = "<!DOCTYPE html><html lang='en'><body><p>" + subject + "</p></body></html>"
    msg_plain = subject

    send_mail(
        subject=subject,
        message=msg_plain,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=msg_html,
    )



def contact_us_email(subject, message, recipient_email):
    send_mail(subject= subject, message= message, html_message=message, from_email = recipient_email, recipient_list= [settings.DEFAULT_FROM_EMAIL,], fail_silently=False)


# Helper functions
def get_organization_summary_email_address(organization_id):
    user_emails = profile.objects.filter(organization_id=organization_id,
                                   custom_user__groups__name="Summary reporter").\
        values_list('custom_user__email', flat=True)
    return user_emails


#TODO make data driven
def get_wsdot_coversheet_reviewer_email():
    return [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov']


#TODO make data driven
def get_wsdot_data_report_reviewer_email():
    return [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov']