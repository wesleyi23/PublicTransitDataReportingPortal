from django import template
from django.conf import settings
from Panacea.models import organization, transit_mode

register = template.Library()



@register.filter
def in_category(things, category):
    things = [i for i in things if i.year == category]
    return things

@register.simple_tag(name = 'get_org_name')
def print_org_name(organization_id):
    name = organization.objects.get(id = organization_id).name
    return name

@register.filter(name='print_long_date_name')
def print_long_date_name(int_month):
    REPORT_MONTH = (
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    )
    return REPORT_MONTH[int_month-1][1]


@register.filter(name='get_status_icon')
def get_status_icon(status):
    if status == "Past due":
        html = '<i class="fas fa-exclamation-triangle text-warning"> Due</i>'
    elif status == "Submitted":
        html = '<i class="fas fa-check-circle text-success"></i>'
    elif status == "Not due yet":
        html = ''
    elif status == "Error":
        html = 'Error'
    else:
        html = 'Error'
    return html


@register.filter(name='plus_one')
def plus_one(int_num):
    return int_num+1


@register.filter(name='minus_one')
def plus_one(int_num):
    return int_num-1


@register.filter(name='get_org_by_custom_user')
def get_org_by_custom_user(profile_data, id):
    output = profile_data.get(custom_user_id=id).organization
    return output


@register.filter(name='get_requested_permissions_by_custom_user')
def get_requested_permissions_by_custom_user(profile_data, id):
    user_data = profile_data.get(custom_user_id=id)

    if user_data.requested_permissions.exists():
        requested_permissions = user_data.requested_permissions.all()
    else:
        requested_permissions = user_data.reports_on.all()
    output = ""
    i = 0
    for item in requested_permissions:
        if i == 0:
            output = item.name
            i += 1
        else:
            output = output + " & " + item.name
    return output


@register.filter(name='get_chart_dataset_data')
def get_chart_data(chart_dict_item):
    return chart_dict_item[0]


@register.filter(name='get_chart_dataset_color')
def get_chart_color(chart_dict_item):
    return chart_dict_item[1]


@register.filter(name='get_boarder_dash')
def get_boarder_dash(chart_dict_item):
    if chart_dict_item[2]:
        return '[]'
    else:
        return '[]'


@register.filter(name='clean_classifications')
def clean_classifications(classifications):
    if len(classifications) == 1:
        return classifications[0] + " Systems"
    if len(classifications) == 2:
        return classifications[0] + " & " + classifications[1] + " Systems"
    if len(classifications) == 3:
        return classifications[0] + ", " + classifications[1] + ", & " + classifications[2] + " Systems"


@register.filter(name='print_dashboard_cards_data')
def print_dashboard_cards_data(data):
    percent = data[1]
    if not isinstance(percent, str):
        percent = round(data[1] * 100, 2)
        if percent < 0:
            percent = "<font class='text-danger'>" + str(percent) + "%</font>"
        else:
            percent = "<font class='text-success'>" + str(percent) + "%</font>"

    return f'{data[0]:,}' + " | " + str(percent)


@register.filter(name='has_group')
def has_group(user, group_name):
    if not settings.ENABLE_PERMISSIONS:
        return True
    return user.groups.filter(name=group_name).exists()


@register.filter
def index(sequence, position):
    return sequence[position]


@register.filter
def transit_mode_from_id(mode_id):
    mode_name = transit_mode.objects.get(id=mode_id).mode
    return mode_name


@register.simple_tag
def define(val=None):
  return val

@register.filter
def get_AutoNumeric_mask_type(metric):
    print(metric)
    return "Int"
