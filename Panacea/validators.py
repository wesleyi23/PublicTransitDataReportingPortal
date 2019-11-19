from django import forms
from django.db import transaction
from .models import transit_data, validation_errors


def exceeds_limits(data1, data2):
    if abs((data2-data1)/data1) >= .15:
        return (data2-data1)/data1
    else:
        return False

def revenue_is_larger_than_total(data1, data2, category1, category2):
    if data1 > data2:
        raise forms.ValidationError(('Please amend the following {} as it exceeds the total listed in this {}').format(category1, category2))



def compare_data_years(report_year_data, previous_year_data, validation_test, validation_keys):
    if report_year_data.filter(transit_metric__name =validation_keys[0]).values('reported_value')[0]['reported_value'] == None and previous_year_data.filter(transit_metric__name=validation_keys[0]).values('reported_value')[0]['reported_value'] == None:
        return False
    else:
        report_year_ratio = report_year_data.filter(transit_metric__name =validation_keys[0]).values('reported_value')[0]['reported_value']/report_year_data.filter(transit_metric__name = validation_keys[1]).values('reported_value')[0]['reported_value']
        previous_year_ratio = previous_year_data.filter(transit_metric__name=validation_keys[0]).values('reported_value')[0]['reported_value']/previous_year_data.filter(transit_metric__name=validation_keys[1]).values('reported_value')[0]['reported_value']
        percent_change = exceeds_limits(previous_year_ratio, report_year_ratio)
        if percent_change != False:
            if percent_change < 0:
                return '{}, which is {} this year, has decreased by {}% from last year, when it was {}. Please revise the following fields: {}, {} or provide an explanation for the change'.format(validation_test, round(report_year_ratio, 2), round(percent_change*100, 2), round(previous_year_ratio, 2), validation_keys[0], validation_keys[1])
            elif percent_change > 0:
                return '{}, which is {} this year, has increased by {}% from last year, when it was {}. Please revise the following fields: {}, {} or provide an explanation for the change'.format(validation_test, round(report_year_ratio,2), round(percent_change*100,2), round(previous_year_ratio, 2), validation_keys[0], validation_keys[1])
        else:
            return False

def check_miles_and_hours(report_year_data):
    error_list = []
    try:
        if report_year_data.filter(transit_metric__name = 'Revenue Vehicle Miles').values('reported_value')[0]['reported_value'] > report_year_data.filter(transit_metric__name = 'Total Vehicle Miles').values('reported_value')[0]['reported_value']:
            error_list.append('Revenue Vehicle Miles is greater than Total Vehicle Miles. Please adjust or make a correction.')
        elif report_year_data.filter(transit_metric__name = 'Revenue Vehicle Hours').values('reported_value')[0]['reported_value'] > report_year_data.filter(transit_metric__name = 'Total Vehicle Hours').values('reported_value')[0]['reported_value']:
            error_list.append('Revenue Vehicle Hours is greater than Total Vehicle Hours. Please adjust or make a correction.')
        elif report_year_data.filter(transit_metric__name = 'Revenue Vessel Miles').exists():
            if report_year_data.filter(transit_metric__name='Revenue Vessel Miles').values('reported_value')[0]['reported_value'] > report_year_data.filter(transit_metric__name = 'Total Vessel Miles').values('reported_value')[0]['reported_value']:
                error_list.append('Revenue Vessel Miles is greater than Total Vessel Miles. Please adjust or make a correction.')
    # this is to deal with the problems caused by all our dummy data
    except TypeError:
        return False
    if error_list == []:
        return False
    else:
        return error_list


#TODO make sure this orders by mode, and returns an error list dictioanry, tied to each mode, so a first function finds them alls out, a second one runs validation
# and then packages them and sends them back

def validation_test_for_transit_data(report_year, mode_id, administration_of_mode, organization, user):
    error_list = []
    validation_test_dictionary = {'Vehicle Revenue Speed': ['Revenue Vehicle Miles', 'Revenue Vehicle Hours'], 'Passenger Trips per Revenue Vehicle Miles': ['Passenger Trips', 'Revenue Vehicle Miles'],
                                  'Cost per Revenue Vehicle Hour':['Operating Expenses', 'Revenue Vehicle Hours'], 'Cost per Revenue Vehicle Mile': ['Operating Expenses', 'Revenue Vehicle Miles'],
                                  'Vehicle Revenue Hours per FTE':['Revenue Vehicle Hours', 'Employees - FTEs'], 'Farebox Revenues per Passenger Trip': ['Farebox Revenues', 'Passenger Trips']}

    previous_year = report_year -1
    report_year_data = transit_data.objects.filter(year = report_year, transit_mode = mode_id, administration_of_mode = administration_of_mode, organization = organization)
    previous_year_data = transit_data.objects.filter(year = previous_year, transit_mode = mode_id, administration_of_mode = administration_of_mode, organization = organization)
    other_errors = check_miles_and_hours(report_year_data)
    if other_errors != False:
        for error in other_errors:
            validation_errors.objects.create(year=report_year, error=error, organization_id=organization, report_by_id=user, administration_of_mode=administration_of_mode, transit_mode_id=mode_id)
    for key, value in validation_test_dictionary.items():
        error = compare_data_years(report_year_data, previous_year_data, key, value)
        if error != False:
            error_list.append(error)
            # I put in unique constraints on this particular combination of things so since this loads up every time we review the data, need a check to look at db errors
            if validation_errors.objects.filter(year = report_year, error = error, organization_id= organization,report_by_id= user, administration_of_mode = administration_of_mode, transit_mode_id= mode_id).exists():
                pass
            # creates an error object
            else:
                validation_errors.objects.create(year = report_year, error = error, organization_id= organization,report_by_id= user, administration_of_mode = administration_of_mode, transit_mode_id= mode_id)
    return error_list











def validate_image_file(file):
    ALLOWED_EXTENSIONS = [".png", ".jpeg", ".jpg", ".tif"]

    valid_ext = False

    for ext in ALLOWED_EXTENSIONS:
        if ext in file.name.lower():
            valid_ext = True

    if not valid_ext:
        raise forms.ValidationError('File type not supported.')


