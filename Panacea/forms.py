from django import forms
from django.contrib.auth import password_validation, login
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm
import datetime
from .models import custom_user, profile, organization, ReportType, vanpool_report, vanpool_expansion_analysis
from django.utils.translation import gettext, gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from localflavor.us.forms import USStateSelect, USZipCodeField
from django.core import serializers
from tempus_dominus.widgets import DatePicker
from .widgets import FengyuanChenDatePickerInput


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
        fields = ('reports_on',)


class VanpoolMonthlyReport(forms.ModelForm):

    def __init__(self, user_organization, record_id, report_month, report_year, *args, **kwargs):
        self.report_month = report_month
        self.report_year = report_year
        self.user_organization = user_organization
        self.record_id = record_id
        super(VanpoolMonthlyReport, self).__init__(*args, **kwargs)

    new_data_change_explanation = forms.CharField(required=False, widget=forms.Textarea(
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
                                'new_data_change_explanation',
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
            raise forms.ValidationError(
                'You must fill out the data for the previous month first. Please refer to the previous reporting month')
            error_list.append(
                'You must fill out the data for the previous month first. Please refer to the previous reporting month')
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

                if new_data >= old_data * 1.2:
                    category = category.replace('_', ' ')
                    category = category.title()
                    error_list.append('{} have increased more than 20%. Please confirm this number.'.format(category))

                # Math error here I changed both to be consistent
                elif new_data <= old_data * 0.8:
                    category = category.replace('_', ' ')
                    category = category.title()
                    error_list.append('{} have decreased more than 20%. Please confirm this number'.format(category))
                if category == 'vanpool_groups_in_operation':
                    old_van_number = vanpool_report.objects.filter(
                        organization_id=self.user_organization,
                        report_year=report_year,
                        report_month=report_month).values('vanpool_groups_in_operation', 'vanpool_group_starts',
                                                          'vanpool_group_folds')
                    old_van_number = old_van_number[0]
                    if new_data != (
                            old_van_number['vanpool_groups_in_operation'] + old_van_number['vanpool_group_starts'] -
                            old_van_number['vanpool_group_folds']):
                        error_list.append(
                            'The Vanpool Groups in Operation do not reflect the folds and started recorded last month')
            return error_list

    def clean(self):
        cleaned_data = super(VanpoolMonthlyReport, self).clean()
        # try except block because acknowledge validation errors only exists after the validation has taken place
        print("Try if results: " + str(cleaned_data['acknowledge_validation_errors']))
        try:
            if cleaned_data['acknowledge_validation_errors']:
                print("clean-return-clean-data")
                return cleaned_data
            else:
                print("else")
                raise NameError('run_validator')
        except:
            print("except")
            error_list = self.validator_method()
            print('error list len: ' + str(len(error_list)))
            if len(error_list) > 0:
                print(error_list)
                raise forms.ValidationError(error_list)
            return cleaned_data

    class Meta:
        model = vanpool_report
        exclude = ('report_date', 'report_year', 'report_month', 'report_by', 'organization', 'report_type',
                   'report_due_date')
        widgets = {
            'vanshare_groups_in_operation': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_group_starts': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_group_folds': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_passenger_trips': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanshare_miles_traveled': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_groups_in_operation': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_group_starts': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_group_folds': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vans_available': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'loaner_spare_vans_in_fleet': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_passenger_trips': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'vanpool_miles_traveled': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'average_riders_per_van': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),
            'average_round_trip_miles': forms.NumberInput(
                attrs={'required': True, 'class': 'form-control input-sm'}),

        }

    # TODO test how easily the fields can be extracted
    def save(self, commit=True):
        print("save")
        instance = super(VanpoolMonthlyReport, self).save(commit=False)
        if self.cleaned_data['new_data_change_explanation'] != None:
            past_explanations = vanpool_report.objects.get(id=instance.id).data_change_explanation
            if past_explanations is None:
                past_explanations = ""
            instance.data_change_explanation = past_explanations + \
                                               "{'edit_date':'" + str(datetime.date.today()) + \
                                               "','explanation':'" + self.cleaned_data[
                                                   'new_data_change_explanation'] + "'},"

            past_data_change_record = vanpool_report.objects.get(id=instance.id).data_change_record
            if past_data_change_record is None:
                past_data_change_record = ""
            instance.data_change_record = past_data_change_record + serializers.serialize('json', [
                vanpool_report.objects.get(id=instance.id), ])
        if commit:
            instance.save()
        return instance


class organization_profile(forms.ModelForm):
    class Meta:
        TRUE_FALSE_CHOICES = (
            (False, 'No'),
            (True, 'Yes')
        )

        model = organization
        fields = ('name', 'address_line_1', 'address_line_2', 'city', 'state', 'zip_code', 'vanshare_program')
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'address_line_1': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'address_line_2': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True', 'style': "width:350px"}),
            'city': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'state': forms.Select(attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True',
                                         'style': 'pointer-events: none'}),
            'zip_code': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'vanshare_program': forms.Select(choices=TRUE_FALSE_CHOICES,
                                             attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True',
                                                    'style': 'pointer-events: none'})
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


class chart_form(forms.Form):
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
                                                               'data-form-name': "chart_form"}))
    chart_organizations = forms.ModelChoiceField(queryset=organization.objects.all(),
                                                 widget=forms.CheckboxSelectMultiple(
                                                     attrs={'class': 'form-check checkbox-grid',
                                                            'data-form-name': "chart_form"}))
    chart_time_frame = forms.CharField(widget=forms.Select(choices=TIMEFRAME_CHOICES,
                                                           attrs={'class': 'form-control my_chart_control',
                                                                  'data-form-name': "chart_form"}))


class submit_a_new_vanpool_expansion(forms.ModelForm):
    queryset = organization.objects.all().order_by('name')
    organization = forms.ModelChoiceField(queryset=queryset,
                                          widget=forms.Select(attrs={'class': 'form-control'}))
    date_of_award = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                        widget=forms.DateInput(attrs={'class': 'form-control'}))
    latest_vehicle_acceptance = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                                    widget=forms.DateInput(attrs={'class': 'form-control'}))

    # TODO is this used?
    def as_myp(self):
        return self._html_output(
            normal_row='<p%(html_class_attr)s>%(label)s</p> <p>%(field)s%(help_text)s</p>',
            error_row='%s',
            row_ender='</p>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=True)

    class Meta:
        model = vanpool_expansion_analysis

        fields = ['organization', 'date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance',
                  'vanpools_in_service_at_time_of_award', 'notes']
        required = ['organization', 'date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance',
                    'extension_granted', 'vanpools_in_service_at_time_of_award', 'expired']

        labels = {'organization': False,
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
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }


class Modify_A_Vanpool_Expansion(forms.ModelForm):
    class Meta:
        model = vanpool_expansion_analysis
        latest_vehicle_acceptance = forms.DateTimeField(input_formats=['%Y-%m-%d'],
                                                        widget=forms.DateInput(attrs={'class': 'form-control'}))

        fields = ['expansion_vans_awarded', 'latest_vehicle_acceptance', 'extension_granted', 'expired', 'notes']
        widgets = {'expansion_vans_awarded': forms.NumberInput(attrs={'class': 'form-control'}),
                   'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'style': 'max-width:600px'}),
                   'extension_granted': forms.CheckboxInput(
                       attrs={'class': 'form-control', 'style': 'width:auto;zoom:200%'}),
                   'expired': forms.CheckboxInput(attrs={'class': 'form-control',
                                                         'style': 'width:auto;zoom:200%;float:left;margin-right:0.5rem',
                                                         'disabled': 'disabled'})
                   }
