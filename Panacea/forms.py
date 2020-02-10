from django import forms
from django.forms import BaseModelFormSet, BaseModelForm, ModelForm
from django.forms.formsets import BaseFormSet
from django.contrib.auth import password_validation, login
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
import datetime

from Panacea.utilities import find_user_organization, find_vanpool_organizations, calculate_percent_change
from .models import custom_user, \
    profile, \
    organization, \
    ReportType, \
    vanpool_report, \
    vanpool_expansion_analysis, \
    cover_sheet, \
    transit_data, expense, revenue, revenue_source, transit_mode, service_offered, transit_metrics, expense_source, \
    fund_balance, fund_balance_type, validation_errors, cover_sheet_review_notes
from django.utils.translation import gettext, gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from localflavor.us.forms import USStateSelect, USZipCodeField
from django.core import serializers
from dateutil.relativedelta import relativedelta
from tempus_dominus.widgets import DatePicker
from .widgets import FengyuanChenDatePickerInput


# region shared
class CustomUserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(
        label=False,
        strip=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=False,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control form-control-user', 'placeholder': 'Enter Password Again'}),
        strip=False,
        help_text=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs.update({'autofocus': True})

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data
        # by super().
        password = self.cleaned_data.get('password2')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error('password2', error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()
        return user

    class Meta:
        model = custom_user
        fields = ('first_name', 'last_name', 'email')
        labels = {
            'first_name': False,
            'last_name': False,
            'email': False,
        }
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'Email Address'}),
        }


class custom_user_ChangeForm(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-user', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control form-control-user', 'placeholder': 'Email Address'}),
        }


class ProfileSetup_PhoneAndOrg(forms.ModelForm):
    class Meta:
        model = profile
        fields = ('telephone_number', 'organization')
        widgets = {
            'telephone_number': forms.TextInput(
                attrs={'class': 'form-control form-control-user'})
        }


class user_profile_custom_user(forms.ModelForm):

    class Meta:
        model = custom_user
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'first_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'email': forms.EmailInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
        }


class user_profile_profile(forms.ModelForm):

    class Meta:
        model = profile
        queryset = organization.objects.all()
        fields = ('telephone_number', 'job_title')
        widgets = {
            'telephone_number': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'job_title': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'})
        }


class PhoneOrgSetup(forms.ModelForm):
    queryset = organization.objects.all().order_by('name')

    telephone_number = PhoneNumberField(widget=forms.TextInput(attrs={'class': 'form-control form-control-user'}),
                                        label=_("Phone number:"), required=True)
    job_title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control form-control-user'}),
                                required=True)
    organization = forms.ModelChoiceField(queryset=queryset,
                                          widget=forms.Select(attrs={'class': 'form-control form-control-user'}))

    class Meta:
        model = profile
        fields = ('telephone_number', 'job_title', 'organization')


class ReportSelection(forms.ModelForm):
    queryset = ReportType.objects.all()

    reports_on = forms.ModelMultipleChoiceField(queryset=queryset, label='',
                                                widget=forms.CheckboxSelectMultiple(choices=queryset,
                                                                                    attrs={'class': 'custom-checkbox'}))

    class Meta:
        model = profile
        fields = ('reports_on', )


class organization_profile(forms.ModelForm):
    class Meta:
        TRUE_FALSE_CHOICES = (
            (False, 'No'),
            (True, 'Yes')
        )

        model = organization
        fields = ('name', 'address_line_1', 'address_line_2', 'city', 'state', 'zip_code', 'vanshare_program',
                  'in_puget_sound_area', 'summary_organization_classifications')
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'address_line_1': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'address_line_2': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'city': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'state': forms.Select(
                attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True',
                       'style': 'pointer-events: none'}),
            'zip_code': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'vanshare_program': forms.Select(choices=TRUE_FALSE_CHOICES,
                                             attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True',
                                                    'style': 'pointer-events: none'}),
            'in_puget_sound_area': forms.Select(choices=TRUE_FALSE_CHOICES,
                                                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                                                       'style': 'pointer-events: none'}),
            'summary_organization_classifications': forms.Select(choices=organization.SUMMARY_ORG_CLASSIFICATIONS,
                                                                 attrs={'class': 'form-control-plaintext',
                                                                        'readonly': 'True',
                                                                        'style': 'pointer-events: none'}),

        }


class change_user_permissions_group(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ['first_name', 'last_name', 'email', 'groups', ]
        widgets = {
            'groups': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline no-bullet AJAX_instant_submit',
                                                          'data-form-name': "Admin_assignPermissions_all"}),
            'first_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                       'style': 'display: none; visibility: hidden'}),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                       'style': 'display: none; visibility: hidden'}),
            'email': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True',
                       'style': 'display: none; visibility: hidden'}),
        }


class request_user_permissions(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ['groups', ]
        widgets = {
            'groups': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'})
        }


class organisation_summary_settings(forms.Form):
    INCLUDE_YEARS_CHOICES = (
        (1, "One Year"),
        (2, "Two Years"),
        (3, "Three Years"),
        (5, "Five Years"),
        (10, "Ten Years"),
        (99, "All")
    )


    include_years = forms.CharField(widget=forms.Select(choices=INCLUDE_YEARS_CHOICES,
                                                        attrs={'class': 'form-control',
                                                               'data-form-name': "vanpool_metric_chart_form"}))
    summary_org = forms.ModelChoiceField(queryset=organization.objects.all(),
                                         widget=forms.Select(attrs={'class': 'form-control',
                                                                    'data-form-name': "vanpool_metric_chart_form"}))
# endregion


# region vanpool
class VanpoolMonthlyReport(forms.ModelForm):

    def __init__(self, user_organization, record_id, report_month, report_year, *args, **kwargs):
        self.report_month = report_month
        self.report_year = report_year
        self.user_organization = user_organization
        self.record_id = record_id
        super(VanpoolMonthlyReport, self).__init__(*args, **kwargs)

    changeReason = forms.CharField(required=False, widget=forms.Textarea(
        attrs={'class': 'form-control input-sm', 'rows': 3, 'display': False})
                                   )

    acknowledge_validation_errors = forms.BooleanField(
        label='Check this box to confirm that your submitted numbers are correct, even though there are validation errors.',
        widget=forms.CheckboxInput(attrs={'class': 'checkbox', 'style': 'zoom:200%;margin-right:.35rem'}),
        required=False)

    def validator_method(self):

        # instantiate the error list
        error_list = []

        # Validation is not run on these fields
        untracked_categories = ['vanpool_group_starts',
                                'vanpool_group_folds',
                                'vans_available',
                                'loaner_spare_vans_in_fleet',
                                'average_riders_per_van',
                                'average_round_trip_miles',
                                'changeReason',
                                'data_change_record',
                                'acknowledge_validation_errors']

        report_month = self.report_month
        report_year = self.report_year
        if report_month == 1:
            report_year = report_year - 1
            report_month = 12
        else:
            report_month = report_month - 1

        vp_ops = vanpool_report.objects.filter(organization_id=self.user_organization,
                                               report_year=report_year,
                                               report_month=report_month).values('vanpool_groups_in_operation')
        if vp_ops[0]['vanpool_groups_in_operation'] == None:
            raise forms.ValidationError('You must fill out the data for the previous month first. Please refer to the previous reporting month')
            error_list.append('You must fill out the data for the previous month first. Please refer to the previous reporting month')
            return error_list
        else:
            for category in self.cleaned_data.keys():
                if self.cleaned_data[category] == None:
                    continue
                if category in untracked_categories:
                    continue

                new_data = self.cleaned_data[category]
                old_data = vanpool_report.objects.filter(organization_id=self.user_organization,
                                                         vanpool_groups_in_operation__isnull=False,
                                                         report_year=report_year,
                                                         report_month=report_month).values(category)
                old_data = old_data[0][category]

                # Should not happen but in case there is old data that is missing a value (came up during testing)
                if old_data is None:
                    continue
                if category == 'vanpool_groups_in_operation':
                    old_van_number = vanpool_report.objects.filter(
                        organization_id=self.user_organization,
                        report_year=report_year,
                        report_month=report_month).values('vanpool_groups_in_operation', 'vanpool_group_starts',
                                                          'vanpool_group_folds')
                    old_van_number = old_van_number[0]
                    if new_data != (
                            int(old_van_number['vanpool_groups_in_operation']) + int(old_van_number['vanpool_group_starts']) -
                            int(old_van_number['vanpool_group_folds'])):
                        old_total = int(old_van_number['vanpool_groups_in_operation']) + int(old_van_number['vanpool_group_starts']) -int(old_van_number['vanpool_group_folds'])
                        error_list.append(
                            'The Vanpool Groups in Operation are not equal to the projected number of vanpool groups in operation of {}, based on the {} fold(s) and {} start(s) recorded last month.'.format(old_total,old_van_number['vanpool_group_starts'], old_van_number['vanpool_group_folds']))

                if category == 'vanshare_groups_in_operation':
                    old_van_number = vanpool_report.objects.filter(
                        organization_id=self.user_organization,
                        report_year=report_year,
                        report_month=report_month).values('vanshare_groups_in_operation', 'vanshare_group_starts',
                                                          'vanshare_group_folds')
                    old_van_number = old_van_number[0]
                    if new_data != (
                            int(old_van_number['vanshare_groups_in_operation']) + int(old_van_number['vanshare_group_starts']) -int(old_van_number['vanshare_group_folds'])):
                        old_total = int(old_van_number['vanshare_groups_in_operation']) + int(old_van_number['vanshare_group_starts']) -int(old_van_number['vanshare_group_folds'])
                        error_list.append(
                            'The Vanshare Groups in Operation are not equal to the projected number of vanshare groups in operation of {}, based on the {} fold(s) and {} start(s) recorded last month.'.format(old_total, old_van_number['vanshare_group_folds'],old_van_number['vanshare_group_starts'] ))

                if new_data > old_data * 1.2:
                    category = category.replace('_', ' ')
                    category = category.title()
                    error_list.append('{} have increased more than 20%. Please confirm this number.'.format(category))

                elif new_data < old_data * 0.8:
                    category = category.replace('_', ' ')
                    category = category.title()
                    error_list.append('{} have decreased more than 20%. Please confirm this number'.format(category))

                if category == 'vanpool_groups_in_operation':
                    old_van_number = vanpool_report.objects.filter(
                        organization_id=self.user_organization,
                        report_year=report_year,
                        report_month=report_month).values('vanpool_groups_in_operation', 'vanpool_group_starts', 'vanpool_group_folds')
                    old_van_number = old_van_number[0]

                    if new_data != (old_van_number['vanpool_groups_in_operation'] + old_van_number['vanpool_group_starts'] - old_van_number['vanpool_group_folds']):
                        error_list.append('The Vanpool Groups in Operation do not reflect the folds and started recorded last month')

            return error_list

    def clean(self):
        cleaned_data = super(VanpoolMonthlyReport, self).clean()
        # try except block because acknowledge validation errors only exists after the validation has taken place
        try:
            if cleaned_data['acknowledge_validation_errors'] == True:
                return cleaned_data
            else:
                raise NameError('run_validator')
        except:
            error_list = self.validator_method()
            if len(error_list) > 0:
                raise forms.ValidationError(error_list)
            return cleaned_data

    class Meta:
        model = vanpool_report
        exclude = ('report_date', 'report_year', 'report_month', 'report_by', 'organization', 'report_type',
                   'report_due_date')
        widgets = {
            'vanshare_groups_in_operation': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_group_starts': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_group_folds': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_passenger_trips': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_miles_traveled': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_groups_in_operation': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_group_starts': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_group_folds': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vans_available': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'loaner_spare_vans_in_fleet': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_passenger_trips': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_miles_traveled': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'average_riders_per_van': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'average_round_trip_miles': forms.TextInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'operating_cost': forms.TextInput(
                attrs={'required': False, 'class': 'form-control input-sm'}),
            'frequency_of_claims': forms.TextInput(
                attrs={'required': False, 'class': 'form-control input-sm'}),

        }

    def save(self, commit=True):
        instance = super(VanpoolMonthlyReport, self).save(commit=False)
        if commit:
            instance.save()
        return instance


# TODO rename this form to something less generic
class vanpool_metric_chart_form(forms.Form):
    MEASURE_CHOICES_DICT = {
        "total_miles_traveled": "Total Miles Traveled",
        "total_passenger_trips": "Total Passenger Trips",
        "average_riders_per_van": "Average Riders per Van",
        "average_round_trip_miles": "Average Round Trip Miles",
        "total_groups_in_operation": "Total Groups in Operation",
        "vans_available": "Vans Available",
        "loaner_spare_vans_in_fleet": "Loaner Spare Vans in Fleet"
    }

    MEASURE_CHOICES = (
        ("total_miles_traveled", "Total Miles Traveled"),
        ("total_passenger_trips", "Total Passenger Trips"),
        ("average_riders_per_van", "Average Riders per Van"),
        ("average_round_trip_miles", "Average Round Trip Miles"),
        ("total_groups_in_operation", "Total Groups in Operation"),
        ("vans_available", "Vans Available"),
        ("loaner_spare_vans_in_fleet", "Loaner Spare Vans in Fleet")
    )

    ORGANIZATION_CHOICES = organization.objects.all().values('name')
    TIMEFRAME_CHOICES = (
        (3, "Three Months"),
        (6, "Six Months"),
        (12, "One Year"),
        (36, "Three Years"),
        (60, "Five Years"),
        (120, "Ten Years"),
        (999, "All")
    )

    chart_measure = forms.CharField(widget=forms.Select(choices=MEASURE_CHOICES,
                                                        attrs={'class': 'form-control my_chart_control',
                                                               'data-form-name': "vanpool_metric_chart_form"}))
    chart_organizations = forms.ModelChoiceField(queryset=find_vanpool_organizations().order_by('name'), empty_label=None,
                                                 widget=forms.CheckboxSelectMultiple(
                                                     attrs={'class': 'form-check checkbox-grid',
                                                            'data-form-name': "vanpool_metric_chart_form"}))
    chart_time_frame = forms.CharField(widget=forms.Select(choices=TIMEFRAME_CHOICES,
                                                           attrs={'class': 'form-control my_chart_control',
                                                                  'data-form-name': "vanpool_metric_chart_form"}))


class statewide_summary_settings(forms.Form):
    INCLUDE_YEARS_CHOICES = (
        (1, "One Year"),
        (2, "Two Years"),
        (3, "Three Years"),
        (5, "Five Years"),
        (10, "Ten Years"),
        (99, "All")
    )

    INCLUDE_REGION_CHOICES = (
        ("Puget Sound", "Puget Sound"),
        ("Outside Puget Sound", "Outside Puget Sound"),
        ("Statewide", "Statewide")
    )

    include_years = forms.CharField(widget=forms.Select(choices=INCLUDE_YEARS_CHOICES,
                                                        attrs={'class': 'form-control',
                                                               'data-form-name': "vanpool_metric_chart_form"}))

    include_regions = forms.CharField(widget=forms.Select(choices=INCLUDE_REGION_CHOICES,
                                                          attrs={'class': 'form-control ',
                                                                 'data-form-name': "vanpool_metric_chart_form"}))
    include_agency_classifications = forms.MultipleChoiceField(choices=organization.AGENCY_CLASSIFICATIONS,
                                                               widget=forms.CheckboxSelectMultiple(
                                                                   attrs={'class': 'form-check',
                                                                          'data-form-name': "vanpool_metric_chart_form"}))


class submit_a_new_vanpool_expansion(forms.ModelForm):
    CHOICES = (
        ('11-13', '11-13'),
        ('13-15', '13-15'),
        ('15-17', '15-17'),
        ('17-19', '17-19'),
        ('19-21', '19-21'),
        ('21-23', '21-23'),
        ('23-25', '23-25'),
        ('25-27', '25-27')
    )

    queryset = organization.objects.all().order_by('name')
    organization = forms.ModelChoiceField(queryset=queryset,
                                          widget=forms.Select(attrs={'class': 'form-control'}))
    date_of_award = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                        widget=forms.DateInput(attrs={'class': 'form-control'}))
    latest_vehicle_acceptance = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                                    widget=forms.DateInput(attrs={'class': 'form-control'}))

    awarded_biennium = forms.CharField(widget=forms.Select(choices = CHOICES, attrs = {'class': 'form-control'}))

    notes = forms.CharField(widget = forms.Textarea(attrs={'class': 'form-control', 'rows':3}), required = False)



    class Meta:
        model = vanpool_expansion_analysis

        fields = ['organization', 'date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance',
                  'vanpools_in_service_at_time_of_award', 'notes', 'award_biennium', 'expansion_goal', 'deadline']
        required = ['organization', 'date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance',
                    'extension_granted', 'vanpools_in_service_at_time_of_award', 'expired', 'vanpool_goal_met']

        labels = {'organization': "Please Select Your Agency",
                  'date_of_award': 'When was the vanpool expansion awarded? Use format YYYY-MM-DD',
                  'expansion_vans_awarded': 'Number of vans awarded in the expansion',
                  'latest_vehicle_acceptance': 'Latest date that vehicle was accepted? Use format YYYY-MM-DD',
                  'extension_granted': 'Extenstion Granted? Set this to no',
                  'vanpools_in_service_at_time_of_award': 'Vanpools in service at time of award',
                  'expired': 'Has the expansion award expired? Set this to no (as it is used later for reporting)',
                  'Notes': False
                  }

        widgets = {
            # 'date_of_award': forms.DateInput(attrs={'class': 'form-control'}),
            'latest_vehicle_acceptance': forms.DateInput(attrs={'class': 'form-control'}),
            'expansion_vans_awarded': forms.NumberInput(attrs={'class': 'form-control'}),
            'vanpools_in_service_at_time_of_award': forms.NumberInput(attrs={'class': 'form-control'}),

        }


class Modify_A_Vanpool_Expansion(forms.ModelForm):
    class Meta:
        model = vanpool_expansion_analysis
        latest_vehicle_acceptance = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                                        widget=forms.DateInput(attrs={'class': 'form-control'}))

        fields = ['expansion_vans_awarded', 'latest_vehicle_acceptance', 'extension_granted', 'expired', 'notes']
        widgets = {'expansion_vans_awarded': forms.NumberInput(attrs={'class': 'form-control'}),
                   'notes': forms.Textarea(attrs={'class': 'form-control', 'rows':3, 'style': 'max-width:600px'}),
                   'extension_granted': forms.CheckboxInput(attrs={'class': 'form-control', 'style': 'width:auto;zoom:200%'}),
                   'expired': forms.CheckboxInput(attrs={'class': 'form-control',
                                                         'style': 'width:auto;zoom:200%;float:left;margin-right:0.5rem',
                                                         'disabled': 'disabled'})
                   }

        #TODO a modal form here for if an extension is granted and one wnated to change the deadline, since at this point the deadline already exists
    def save(self, commit=True):
        instance = super(Modify_A_Vanpool_Expansion, self).save(commit=False)
        self.cleaned_data['deadline'] = self.cleaned_data['latest_vehicle_acceptance'] + relativedelta(months=+18)
        if commit:
            instance.save()
        return instance
# endregion


# region summary

class organization_information(forms.ModelForm):
    class Meta:
        model = organization
        fields = ("summary_organization_classifications", )
        widgets = {
            'summary_organization_classifications': forms.Select(choices=organization.SUMMARY_ORG_CLASSIFICATIONS,
                                                                 attrs={'class': 'form-control form-control-plaintext',
                                                                        'readonly': 'True',
                                                                        'style': 'pointer-events: none'}),
        }

class cover_sheet_organization(forms.ModelForm):
    organization_logo_input = forms.FileField(required=False,
                                              widget=forms.FileInput(attrs={'class': 'my-custom-file-input',
                                                                            'accept': '.jpg, .jpeg, .png, .tif'}))

    class Meta:
        model = cover_sheet
        fields = ['executive_officer_first_name', 'executive_officer_last_name', 'executive_officer_title', 'service_website_url',
                  'service_area_description', 'congressional_districts', 'legislative_districts', 'type_of_government',
                  'governing_body']
        widgets = {
            'executive_officer_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_title': forms.TextInput(attrs={'class': 'form-control'}),
            'service_website_url': forms.URLInput(attrs={'class': 'form-control',
                                                         'label': 'Service website URL'}),
            'service_area_description': forms.TextInput(attrs={'class': 'form-control'}),
            'congressional_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'legislative_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of_government': forms.TextInput(attrs={'class': 'form-control'}),
            'governing_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_organization_logo_input(self):
        from Panacea.validators import validate_image_file
        image = self.cleaned_data.get('organization_logo_input')
        # import pdb; pdb.set_trace()

        print(image)
        if image is not None:
            print("validator")
            validate_image_file(image)

class service_offered_form(forms.ModelForm):

    class Meta:
        model = service_offered
        fields = ['administration_of_mode', 'transit_mode']
        widgets = {
            'transit_mode': forms.Select(choices=transit_mode.objects.all(), attrs={'class': 'form-control'}),
            'administration_of_mode': forms.Select(choices=service_offered.DO_OR_PT, attrs={'class': 'form-control'})
        }


class cover_sheet_service(forms.ModelForm):
    class Meta:
        model = cover_sheet
        fields = ['intermodal_connections', 'fares_description', 'service_and_eligibility',
                  'days_of_service', 'current_operations', 'revenue_service_vehicles',
                  'tax_rate_description']
        widgets = {
            'intermodal_connections': forms.Textarea(attrs={'class': 'form-control'}),
            'fares_description': forms.Textarea(attrs={'class': 'form-control'}),
            'service_and_eligibility': forms.Textarea(attrs={'class': 'form-control'}),
            'days_of_service': forms.TextInput(attrs={'class': 'form-control'}),
            'current_operations': forms.Textarea(attrs={'class': 'form-control'}),
            'revenue_service_vehicles': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate_description': forms.Textarea(attrs={'class': 'form-control'}),
        }

class cover_sheet_wsdot_review(forms.ModelForm):
    organization_logo_input = forms.FileField(required=False,
                                              widget=forms.FileInput(attrs={'class': 'my-custom-file-input',
                                                                            'accept': '.jpg, .jpeg, .png, .tif'}))

    class Meta:
        model = cover_sheet
        exclude = ['id', 'organization', 'transit_development_plan_url', 'monorail_ownership', 'community_planning_region',]

        widgets = {
            'executive_officer_first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'executive_officer_title': forms.TextInput(attrs={'class': 'form-control'}),
            'service_website_url': forms.URLInput(attrs={'class': 'form-control',
                                                         'label': 'Service website URL'}),
            'service_area_description': forms.TextInput(attrs={'class': 'form-control'}),
            'congressional_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'legislative_districts': forms.TextInput(attrs={'class': 'form-control'}),
            'type_of_government': forms.TextInput(attrs={'class': 'form-control'}),
            'governing_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'transit_mode': forms.Select(choices=transit_mode.objects.all(), attrs={'class': 'form-control'}),
            'administration_of_mode': forms.Select(choices=service_offered.DO_OR_PT, attrs={'class': 'form-control'}),
            'intermodal_connections': forms.Textarea(attrs={'class': 'form-control'}),
            'fares_description': forms.Textarea(attrs={'class': 'form-control'}),
            'service_and_eligibility': forms.Textarea(attrs={'class': 'form-control'}),
            'days_of_service': forms.TextInput(attrs={'class': 'form-control'}),
            'current_operations': forms.Textarea(attrs={'class': 'form-control'}),
            'revenue_service_vehicles': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate_description': forms.Textarea(attrs={'class': 'form-control'}),
        }

    def clean_organization_logo_input(self):
        from Panacea.validators import validate_image_file
        image = self.cleaned_data.get('organization_logo_input')
        # import pdb; pdb.set_trace()

        print(image)
        if image is not None:
            print("validator")
            validate_image_file(image)

class add_cover_sheet_review_note(forms.ModelForm):
    class Meta:
        model = cover_sheet_review_notes
        fields = ['note', ]
        widgets = {
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows':2}),
        }

class FormsetCleaner(BaseFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def clean(self):
        """
        Adds validation to check that no two links have the same anchor or URL
        and that all links have both an anchor and URL.
        """
        if any(self.errors):
            return


class summary_expense_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    expense_source = forms.ModelChoiceField(disabled=True, queryset=expense_source.objects.all())
    year = forms.IntegerField(disabled=True)

    class Meta:
        model = expense
        fields = ["id", "expense_source", "year", "reported_value", "comments"]
        widgets = {
            'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class fund_balance_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    fund_balance_type = forms.ModelChoiceField(disabled=True, queryset=fund_balance_type.objects.all())
    year = forms.IntegerField(disabled=True)

    class Meta:
        model = fund_balance
        fields = ["id", "fund_balance_type", "year", "reported_value", "comments"]
        widgets = {
            'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class summary_revenue_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    revenue_source = forms.ModelChoiceField(disabled=True, queryset=revenue_source.objects.all())
    year = forms.IntegerField(disabled=True)

    class Meta:
        model = revenue
        fields = ["id", "revenue_source", "year", "reported_value", "comments"]
        queryset = revenue_source.objects.all()
        widgets = {
            'specific_revenue_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class transit_data_form(forms.ModelForm):

    id = forms.IntegerField(disabled=True)
    metric = forms.ModelChoiceField(disabled=True, queryset=transit_metrics.objects.all())
    year = forms.IntegerField(disabled=True)

    def clean(self):
        cleaned_data = super(transit_data_form, self).clean()
        current_year = datetime.now().year-1
        if cleaned_data['year'] == current_year:
            if cleaned_data['metric_value'] == None:
                pass
            else:
                previous_year = current_year -1
                org_id  = cleaned_data['id'].__getattribute__('organization_id')
                metric_id = cleaned_data['id'].__getattribute__('metric_id')
                mode_id = cleaned_data['id'].__getattribute__('mode_id')
                previous_metric_value = transit_data.objects.filter(organization_id=org_id, metric_id = metric_id, year= previous_year, mode_id = mode_id).values('metric_value')
                percent_change = calculate_percent_change(cleaned_data['metric_value'], previous_metric_value[0]['metric_value'])
                if percent_change > 15 and cleaned_data['comments'] == '':
                    raise forms.ValidationError('The following data has increased more than 15%. Please revise the data or provide an explanatory comment')
                elif percent_change < -15 and cleaned_data['comments'] == '':
                    raise forms.ValidationError('The following data has declined more than 15%. Please revise the data or provide an explanatory comment')
            return cleaned_data
        else:
            return cleaned_data

    class Meta:
        model = transit_data
        fields = ['id', 'transit_metric', 'year', 'reported_value', 'comments']
        widgets = {
            'reported_value': forms.TextInput(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
        }


class validation_error_form(forms.ModelForm):
    class Meta:
        model = validation_errors
        fields = ['error_resolution', 'year', 'error', 'administration_of_mode', 'transit_mode']
        widgets = {
            'error_resolution': forms.Textarea(attrs={'class': 'form-control', "rows": 3}),
            'year': forms.NumberInput(attrs = {'class': 'form-control', 'readonly': 'readonly'}),
            'error': forms.Textarea(attrs={'rows':3, 'readonly': 'readonly'}),
            'administration_of_mode': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'transit_mode': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'id': forms.NumberInput(attrs={ 'class': 'form-control','readonly':'readonly'})
        }

class email_contact_form(forms.Form):
    from_email = forms.EmailField(required=True, label="Sender Email")
    subject = forms.CharField(required=True, label="Subject of Message")
    message = forms.CharField(widget=forms.Textarea, required=True)


# class source_id_formset(BaseModelFormSet):
#     def __init__(self, source_ids, year, my_user, *args, **kwargs):
#         super(source_id_formset, self).__init__(*args, **kwargs)
#         self.source_ids = source_ids
#         self.year = year
#         self.my_user = my_user
#
#     def get_form_kwargs(self, form_index):
#         form_kwargs = super(source_id_formset, self).get_form_kwargs(form_index)
#         if form_index < len(self.source_ids):
#             form_kwargs = {'source_id': self.source_ids[form_index],
#                            'year': self.year,
#                            'my_user': self.my_user}
#         else:
#             form_kwargs = {'source_id': None,
#                            'year': self.year,
#                            'my_user': self.my_user}
#
#         print(form_kwargs)
#         return form_kwargs


# class summary_expense_form(base_summary_expense_form):
#
#     def __init__(self, year, my_user, source_id, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.source_id = source_id
#         self.year = year
#         self.my_user = my_user
#
#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         instance.specific_expense_source_id = self.source_id
#         instance.organization = find_user_organization(self.my_user.id)
#         instance.year = self.year
#         instance.report_by = self.my_user
#         instance.save()


# endregion


class change_user_org(forms.ModelForm):
    class Meta:
        model = profile
        fields = ['custom_user', 'organization']
        widgets = {
            'custom_user': forms.Select(),
            'organization': forms.Select(),
        }