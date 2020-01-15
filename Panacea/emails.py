from .models import custom_user
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



def active_permissions_request_notification():
    if settings.dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL,'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov' ]
    else:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, 'schumen@wsdot.wa.gov', 'wesleyi@wsdot.wa.gov']

    msg_html = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
    msg_plain = "There is an active permissions request in the Public Transportation Reporting Portal"  # TODO add link
    send_mail(
        subject='Active Permissions Request - Public Transportation Reporting Portal',
        message=msg_plain,
        from_email= 'permissions@ptreportingportal.gov',
        recipient_list= recipient_list,
        html_message= msg_html, fail_silently=False)


def notify_user_that_permissions_have_been_requested(full_name, groups, email):
    if settings.dev_mode == True:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, ]
    else:
        recipient_list = [settings.DEFAULT_FROM_EMAIL, ]

    msg_html = render_to_string('emails/request_permissions_email.html',
                                {'user_name': full_name, 'groups': groups})
    msg_plain = render_to_string('emails/request_permissions_email.txt',
                                 {'user_name': full_name, 'groups': groups})
    send_mail(
        subject='Active Permissions Request - Public Transportation Reporting Portal',
        message=msg_plain,
        from_email= settings.DEFAULT_FROM_EMAIL,
        recipient_list = [email,],
        html_message=msg_html,
    )