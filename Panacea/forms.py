from django import forms
from django.contrib.auth import password_validation, login
from django.contrib.auth.forms import UserChangeForm, AuthenticationForm

from .models import custom_user, profile, organization, ReportType, vanpool_report, vanpool_expansion_analysis
from django.utils.translation import gettext, gettext_lazy as _
from phonenumber_field.formfields import PhoneNumberField
from localflavor.us.forms import USStateSelect, USZipCodeField
from tempus_dominus.widgets import DatePicker


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


class PhoneOrgSetup(forms.ModelForm):
    queryset = organization.objects.all()

    telephone_number = PhoneNumberField(widget=forms.TextInput(attrs={'class': 'form-control form-control-user'}),
                                        label=_("Phone number:"), required=True)
    organization = forms.ModelChoiceField(queryset=queryset,
                                          widget=forms.Select(attrs={'class': 'form-control form-control-user'}))

    class Meta:
        model = profile
        fields = ('telephone_number', 'organization')


class ReportSelection(forms.ModelForm):
    queryset = ReportType.objects.all()

    reports_on = forms.ModelMultipleChoiceField(queryset=queryset, label='',
                                                widget=forms.CheckboxSelectMultiple(choices=queryset,
                                                                                    attrs={'class': 'custom-checkbox'}))

    class Meta:
        model = profile
        fields = ('reports_on', )


class VanpoolMonthlyReport(forms.ModelForm):

    class Meta:
        model = vanpool_report
        exclude = ('report_date', 'report_year', 'report_month', 'report_by', 'organization', 'report_type',
                   'report_due_date')
        widgets = {
            'vanshare_groups_in_operation': forms.NumberInput(attrs={'class': 'form-control input-sm'}),
            'vanshare_group_starts': forms.NumberInput(attrs={'class': 'form-control input-sm'}),
            'vanshare_group_folds': forms.NumberInput(attrs={'class': 'form-control form-control-user input-sm'}),
            'vanshare_passenger_trips': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'vanshare_miles_traveled': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'vanpool_groups_in_operation': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'vanpool_group_starts': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'vanpool_group_folds': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'vans_available': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'loaner_spare_vans_in_fleet': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'vanpool_passenger_trips': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'vanpool_miles_traveled': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'average_riders_per_van': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
            'average_round_trip_miles': forms.NumberInput(
                attrs={'class': 'form-control input-sm'}),
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
        fields = ('telephone_number', )
        widgets = {
            'telephone_number': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'})
        }

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
            'state': forms.Select(attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True', 'style': 'pointer-events: none'}),
            'zip_code': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'vanshare_program': forms.Select(choices=TRUE_FALSE_CHOICES, attrs={'class': 'form-control form-control-plaintext', 'readonly': 'True', 'style': 'pointer-events: none'})
        }



class change_user_permissions_group(forms.ModelForm):
    class Meta:
        model = custom_user
        fields = ['first_name', 'last_name', 'email', 'groups', ]
        widgets = {
            'groups': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-inline no-bullet AJAX_instant_submit',
                                                          'data-form-name': "Admin_assignPermissions_all"}),
            'first_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'last_name': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
            'email': forms.TextInput(
                attrs={'class': 'form-control-plaintext', 'readonly': 'True'}),
        }


class submit_a_new_vanpool_expansion(forms.ModelForm):
    queryset = organization.objects.all()
    organization = forms.ModelChoiceField(queryset=queryset,
                                          widget=forms.Select(attrs={'class': 'form-control form-control-user'}))

    def as_myp(self):
        "Returns this form rendered as HTML <p>s."
        return self._html_output(
            normal_row='<p%(html_class_attr)s>%(label)s</p> <p>%(field)s%(help_text)s</p>',
            error_row='%s',
            row_ender='</p>',
            help_text_html=' <span class="helptext">%s</span>',
            errors_on_separate_row=True)


    class Meta:

        model = vanpool_expansion_analysis
        fields = ['organization', 'date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance', 'extension_granted', 'vanpools_in_service_at_time_of_award','expired', 'notes']
        required = ['organization','date_of_award', 'expansion_vans_awarded', 'latest_vehicle_acceptance', 'extension_granted', 'vanpools_in_service_at_time_of_award','expired']

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
             'date_of_award':forms.DateInput(),
            'latest_vehicle_acceptance': forms.DateInput(),
            'expansion_vans_awarded': forms.NumberInput(),
            'vanpools_in_service_at_time_of_award': forms.NumberInput(),

        }


class Modify_A_Vanpool_Expansion(forms.ModelForm):

    class Meta:
        model = vanpool_expansion_analysis
        fields = ['expansion_vans_awarded', 'latest_vehicle_acceptance', 'notes']
        widgets = {'expansion_vans_awarded':forms.NumberInput(), 'latest_vehicle_acceptance': forms.DateInput(), 'notes': forms.TextInput()}
