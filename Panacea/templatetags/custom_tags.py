from django import template

register = template.Library()


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


@register.filter(name='get_reports_on_by_custom_user')
def get_reports_on_by_custom_user(profile_data, id):
    requested_permisions = profile_data.get(custom_user_id=id).reports_on.all()
    output = ""
    i = 0
    for item in requested_permisions:
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


@register.filter(name='print_dashboard_cards_data')
def print_dashboard_cards_data(data):
    percent = data[1]
    if not isinstance(percent, str):
        percent = round(data[1] * 100, 2)
        if percent < 0:
            percent = "<font class='text-danger'>" + str(percent) + "%</font>"
        else:
            percent = "<font class='text-success'>" + str(percent) + "%</font>"

    return str(data[0]) + " | (" + str(percent) + ")"
