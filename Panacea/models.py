from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group  ## A new class is imported. ##
from django.core.validators import MaxValueValidator
from django.db import models
from django.db.models.functions import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField
import datetime


from simple_history.models import HistoricalRecords

# region shared
class CustomUserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class custom_user(AbstractUser):
    # User authentication from tut located here:https://wsvincent.com/django-custom-user-model-tutorial/
    username = None
    email = models.EmailField(_('email address'), unique=True)  # changes email to unique and blank to false
    saw_id = models.CharField(max_length=255, blank=True, null=True)
    wsdot_sso_id = models.CharField(max_length=255, blank=True, null=True)
    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', ]

    def __str__(self):
        return self.email


class ReportType(models.Model):
    def __str__(self):
        return self.name

    REPORT_FREQUENCY = (
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Yearly', 'Yearly'),
        ('Other', 'Other')
    )

    name = models.CharField(max_length=100)
    report_frequency = models.CharField(max_length=50,
                                        choices=REPORT_FREQUENCY,
                                        default='Yearly')
    due_date = models.DateField()
    report_owner = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)


class summary_organization_type(models.Model):
    ORGANIZATION_TYPES = (
        ("Community provider", "Community provider"),
        ("Ferry", "Ferry"),
        ("Intercity bus", "Intercity bus"),
        ("Medicaid broker", "Medicaid broker"),
        ("Monorail", "Monorail"),
        ("Transit", "Transit"),
        ("Tribe", "Tribe"),
    )

    name = models.CharField(max_length=120, choices=ORGANIZATION_TYPES)

    def __str__(self):
        return self.name


class organization(models.Model):
    AGENCY_CLASSIFICATIONS = (
        ("Urban", "Urban"),
        ("Small Urban", "Small Urban"),
        ("Rural", "Rural"),
    )
    # TODO move to table
    SUMMARY_ORG_CLASSIFICATIONS = (
        ("Community provider", "Community provider"),
        ("Ferry", "Ferry"),
        ("Intercity bus", "Intercity bus"),
        ("Medicaid broker", "Medicaid broker"),
        ("Monorail", "Monorail"),
        ("Transit", "Transit"),
        ("Tribe", "Tribe"),
    )

    def __str__(self):
        return self.name

    name = models.CharField(max_length=80, blank=True)
    address_line_1 = models.CharField(max_length=50, blank=True)
    address_line_2 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)
    classification = models.CharField(max_length=50, choices=AGENCY_CLASSIFICATIONS, blank=True, null=True)
    vanpool_program = models.BooleanField(blank=True, null=True, default=True)
    vanshare_program = models.BooleanField(blank=True, null=True)
    vanpool_expansion = models.BooleanField(blank=True, null=True)
    # TODO add to agency profile form
    in_jblm_area = models.BooleanField(blank=True, null=True)  # TODO confirm this is no longer needed
    in_puget_sound_area = models.BooleanField(blank=True, null=True)
    summary_reporter = models.BooleanField(default=True)
    summary_organization_classifications = models.ForeignKey(summary_organization_type, on_delete=models.PROTECT, blank=True, null=True)
    #fixed_route_expansion = models.BooleanField(blank=True, null=True)


#class vanpool_details(models.Model):
 #   organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name="+")
  #  vanpool_program_start_date = models.DateField(blank=True, null=True)
   # vanpool_program_end_date = models.DateField(blank=True, null= True)


class profile(models.Model):
    custom_user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    profile_submitted = models.BooleanField(default=False)
    profile_complete = models.BooleanField(default=False)
    telephone_number = PhoneNumberField(blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    address_line_1 = models.CharField(max_length=50, blank=True)
    address_line_2 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)
    reports_on = models.ManyToManyField(ReportType, blank=True)  # TODO rename this to something else
    requested_permissions = models.ManyToManyField(Group, blank=True)
    active_permissions_request = models.BooleanField(blank=True, null=True)

@receiver(post_save, sender=custom_user)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile.objects.create(custom_user=instance)


@receiver(post_save, sender=custom_user)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()




# endregion


# region Vanpool
class vanpool_report(models.Model):
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

    report_type = models.ForeignKey(ReportType, on_delete=models.PROTECT)
    report_year = models.IntegerField()
    report_month = models.IntegerField(choices=REPORT_MONTH)
    # TODO we should come back and look at if these need to be here
    # report_due_date = models.DateField()
    #report_day = models.IntegerField(default = 1, null=True)
    report_date = models.DateTimeField(default=None, null=True)
    update_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT)
    vanshare_groups_in_operation = models.IntegerField(blank=True, null=True)
    vanshare_group_starts = models.IntegerField(blank=True, null=True)
    vanshare_group_folds = models.IntegerField(blank=True, null=True)
    vanshare_passenger_trips = models.IntegerField(blank=True, null=True)
    vanshare_miles_traveled = models.FloatField(blank=True, null=True)
    vanpool_groups_in_operation = models.IntegerField(blank=True, null=True)
    vanpool_group_starts = models.IntegerField(blank=True, null=True)
    vanpool_group_folds = models.IntegerField(blank=True, null=True)
    vans_available = models.IntegerField(blank=True, null=True)
    loaner_spare_vans_in_fleet = models.IntegerField(blank=True, null=True)
    vanpool_passenger_trips = models.IntegerField(blank=True, null=True)
    vanpool_miles_traveled = models.FloatField(blank=True, null=True)
    average_riders_per_van = models.FloatField(blank=True, null=True, validators=[MaxValueValidator(15)])
    average_round_trip_miles = models.FloatField(blank=True, null=True)
    frequency_of_claims = models.FloatField(blank=True, null=True)
    operating_cost = models.FloatField(blank=True, null=True)
    history = HistoricalRecords()

    @property
    def report_due_date(self):
        month = self.report_month
        year = self.report_year + month // 12
        month = month % 12 + 1
        day = 1
        return datetime.date(year, month, day)


    @property
    def status(self):
        if self.report_date is None:
            if datetime.datetime.now().date() > self.report_due_date:
                return "Past due"
            else:
                return "Not due yet"
        elif self.report_date is not None:
            return "Submitted"
        else:
            return "Error"



    @property
    def report_year_month_label(self):
        return str(self.report_year) + " - " + str(self.report_month)

    @property
    def total_miles_traveled(self):
        result = sum(filter(None, {self.vanpool_miles_traveled, self.vanshare_miles_traveled}))
        if result == 0:
            result = None
        return result

    @property
    def total_passenger_trips(self):
        result = sum(filter(None, {self.vanpool_passenger_trips, self.vanshare_passenger_trips}))
        if result == 0:
            result = None
        return result

    @property
    def total_groups_in_operation(self):
        result = sum(filter(None, {self.vanpool_groups_in_operation, self.vanshare_groups_in_operation}))
        if result == 0:
            result = None
        return result

    def save(self, no_report_date=False, *args, **kwargs):
        if not no_report_date and self.report_date is None:
            self.report_date = datetime.datetime.now().date()
        super(vanpool_report, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('organization', 'report_year', 'report_month',)



class vanpool_expansion_analysis(models.Model):
    # TODO change to our biennium function
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

    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    vanpools_in_service_at_time_of_award = models.IntegerField(blank=True, null=True)
    date_of_award = models.DateField(blank=True, null=True)
    expansion_vans_awarded = models.IntegerField(blank=True, null=True)
    latest_vehicle_acceptance = models.DateField(blank=True, null=True)
    extension_granted = models.BooleanField(blank=False, null=True)
    vanpool_goal_met = models.BooleanField(blank=False, null=True)
    expired = models.BooleanField(blank=False, null=True)
    notes = models.TextField(blank=False, null=True)
    award_biennium = models.CharField(max_length=50, choices=CHOICES, blank=True, null=True)
    expansion_goal = models.IntegerField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    service_goal_met_date = models.DateField(blank=True, null=True)
    max_vanpool_numbers = models.IntegerField(blank=True, null=True)
    max_vanpool_date = models.DateField(blank=True, null=True)
    latest_vanpool_number = models.IntegerField(blank=True, null=True)
    latest_report_date = models.DateField(blank=True, null=True)
    months_remaining = models.CharField(blank=True, null=True, max_length=20)
    organization_name = models.CharField(blank=True, null=True, max_length=100)
    history = HistoricalRecords()

    @property
    def adjusted_service_goal(self):
        return int(self.vanpools_in_service_at_time_of_award + round(self.expansion_vans_awarded*.8, 0))

    #TODO Change all the forms so we get good data, put various checks into the views page,
    @property
    def calculate_current_biennium(self):
        import datetime
        from Panacea.utilities import calculate_biennium
        return calculate_biennium(datetime.date.today())

# endregion


class revenue_source(models.Model):
    LEVIATHANS = (
        ('Federal', 'Federal'),
        ('State', 'State'),
        ('Local', 'Local'),
        ('Other', 'Other')
    )

    FUNDING_KIND = (
        ('Capital', 'Capital'),
        ('Operating', 'Operating'),
        ('Other', 'Other')
    )

    TRUE_FALSE_CHOICES = (
        (True, 'inactive'),
        (False, 'active')
    )

    name = models.CharField(max_length=120, null=True, blank=True)
    order_in_summary = models.IntegerField(null=True, blank=True)
    government_type = models.CharField(max_length=100, choices=LEVIATHANS, null=True, blank=True)
    funding_type = models.CharField(max_length=30, choices=FUNDING_KIND, null=True, blank=True)
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)
    inactive_flag = models.BooleanField(default=False, choices=TRUE_FALSE_CHOICES)
    help_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class revenue(models.Model):
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    revenue_source = models.ForeignKey(revenue_source, on_delete=models.PROTECT, related_name='+')
    reported_value = models.FloatField(null=True, blank=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    history = HistoricalRecords()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together=('organization', 'year', 'revenue_source', )


class expense_source(models.Model):
    name = models.CharField(max_length=100)
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)
    help_text = models.TextField(blank=True, null=True)
    order_in_summary = models.IntegerField(blank=True, null=True)
    heading = models.CharField(max_length=200, blank = True, null = True)

    def __str__(self):
        return self.name


class expense(models.Model):

    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    expense_source = models.ForeignKey(expense_source, on_delete=models.PROTECT, related_name='+')
    reported_value = models.IntegerField(blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    history = HistoricalRecords()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('organization', 'year', 'expense_source', )


class transit_metrics(models.Model):
    FORM_MASKING_CLASSES = (
        ("Int", "Int"),
        ("Float", "Float"),
        ("Money", "Money"),
    )

    name = models.CharField(max_length=120)
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)
    order_in_summary = models.IntegerField(null=True, blank=True)
    form_masking_class = models.CharField(max_length=25, choices=FORM_MASKING_CLASSES, null=True, blank=True)
    help_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class transit_mode(models.Model):
    name = models.CharField(max_length=90, blank=True)
    rollup_mode = models.CharField(max_length=90, blank=True, null=True)

    def __str__(self):
        return self.name


class transit_data(models.Model):

    DO_OR_PT = (
        ('Direct Operated', 'Direct Operated'),
        ('Purchased', 'Purchased')
    )

    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    transit_mode = models.ForeignKey(transit_mode, on_delete=models.PROTECT, related_name='+')
    administration_of_mode = models.CharField(max_length=80, choices=DO_OR_PT)
    transit_metric = models.ForeignKey(transit_metrics, on_delete=models.PROTECT, related_name='+')
    reported_value = models.FloatField(blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()


    class Meta:
        unique_together = ('year', 'transit_mode', 'transit_metric', 'organization', 'administration_of_mode')


class fund_balance_type(models.Model):
    name = models.CharField(max_length=100)
    agency_classification = models.ManyToManyField(summary_organization_type, blank=True)
    help_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class fund_balance(models.Model):
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name='+')
    year = models.IntegerField()
    fund_balance_type = models.ForeignKey(fund_balance_type, on_delete=models.PROTECT, related_name='+')
    reported_value = models.IntegerField(blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('organization', 'year', 'fund_balance_type', )


class cover_sheet(models.Model):
    organization = models.OneToOneField(organization, on_delete=models.PROTECT, blank=True, null=True)
    executive_officer_first_name = models.CharField(max_length=50, blank=True, null=True)
    executive_officer_last_name = models.CharField(max_length=50, blank=True, null=True)
    executive_officer_title = models.TextField(max_length=200, blank=True, null=True)
    service_website_url = models.URLField(verbose_name="Service website URL", max_length=255, blank=True, null=True)
    service_area_description = models.CharField(max_length=500, blank=True, null=True)
    congressional_districts = models.CharField(max_length=100, blank=True, null=True)
    legislative_districts = models.CharField(max_length=100, blank=True, null=True)
    type_of_government = models.CharField(max_length=100, blank=True, null=True)
    governing_body = models.TextField(blank=True, null=True)
    tax_rate_description = models.TextField(blank=True, null=True)
    transit_development_plan_url = models.CharField(verbose_name="Transit development plan URL", max_length=250, blank=True, null=True)
    intermodal_connections = models.TextField(verbose_name="Connections to other systems", blank=True, null=True)
    fares_description = models.TextField(blank=True, null=True)
    service_and_eligibility = models.TextField(verbose_name="Service and eligibility description", blank=True, null=True)
    current_operations = models.TextField(blank=True, null=True)
    revenue_service_vehicles = models.TextField(verbose_name="Revenue service vehicles", blank=True, null=True)
    days_of_service = models.CharField(verbose_name="Days of service", max_length=250, blank=True, null=True)
    monorail_ownership = models.CharField(max_length=250, blank=True, null=True)
    community_planning_region = models.CharField(verbose_name= 'Planning Regions',max_length=1000, blank=True, null=True)
    organization_logo = models.BinaryField(editable=True, blank=True, null=True)
    #organization_logo = models.TextField(blank=True, null=True)
    published_version = models.BooleanField(blank=True, null=True, default=False)
    tax_rate_valid = models.BooleanField(verbose_name="Tax rate information is correct", default=True)
    tax_rate_comment = models.TextField(verbose_name="If tax rate is invalid please provide more information", blank=True, null=True)
    history = HistoricalRecords()
    updated_at = models.DateTimeField(auto_now=True)



    def is_identical_to_published_version(self):
        try:
            db_record = cover_sheet.objects.get(id=self.id)
        except:
            return False

        published_record = cover_sheet.history.filter(id=self.id, published_version=True).order_by('-history_date').first()
        if not published_record:
            if db_record.published_version:
                print('using db_record')
                published_record = db_record
            else:
                return False

        new_values = [(k, v) for k, v in self.__dict__.items() if k != '_state' and k != "published_version"]
        equals_published_record = True
        for key, value in new_values:
            if not published_record.__dict__[key] == value:
                equals_published_record = False

        return equals_published_record

    def save(self, *args, **kwargs):
        self.published_version = self.is_identical_to_published_version()
        super(cover_sheet, self).save(*args, **kwargs)


class service_offered(models.Model):
    DO_OR_PT = (
        ('Direct Operated', 'Direct Operated'),
        ('Purchased', 'Purchased')
    )
    transit_mode = models.ForeignKey(transit_mode, on_delete=models.PROTECT, related_name ='+', blank=False)
    administration_of_mode = models.CharField(max_length=80, choices=DO_OR_PT, blank=False)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=False, null=False)
    service_mode_discontinued = models.BooleanField(default=False, blank=False, null=False)

    class Meta:
        unique_together = ('organization', 'transit_mode', 'administration_of_mode')








class depreciation(models.Model):
    reported_value = models.IntegerField(blank =False, null=True)
    year = models.IntegerField(blank=True, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    comments = models.TextField(blank=True, null=True)
    history = HistoricalRecords()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ('organization', 'year', 'reported_value')




class validation_errors(models.Model):
    DO_OR_PT = (
        ('Direct Operated', 'Direct Operated'),
        ('Purchased', 'Purchased') )
    year = models.IntegerField(blank=True, null=True)
    transit_mode = models.ForeignKey(transit_mode, on_delete=models.PROTECT, related_name= '+', blank=True, null=True)
    administration_of_mode = models.CharField(max_length=80, choices=DO_OR_PT, blank=False, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    error = models.TextField(blank=True, null=True, )
    error_resolution = models.TextField(blank=True, null=True)


class stylesheets(models.Model):
    transit_revenue = models.CharField(max_length = 200, blank=True, null = True)
    transit_expense = models.CharField(max_length=200, blank=True, null= True)
    ferry_expense = models.CharField(max_length=200, blank=True, null= True)
    ferry_revenue = models.CharField(max_length=200, blank=True, null= True)
    transit_data = models.CharField(max_length=200, blank=True, null=True)
    ferry_data = models.CharField(max_length=200, blank=True, null=True)


#class statewide_measures(models.Model):
 #   title = models.CharField(max_length= 200, null=True, blank=True)
  #  transit_data_files = models.CharField(max_length=500, blank=True, null=True)
   # data_type = models.CharField(max_length=40, null=True, blank=True)
    #measure_type = models.CharField(max_length=40, null=True, blank = True)


class service_area_population(models.Model):
    population = models.IntegerField(blank=False, null=False)
    year = models.IntegerField(blank=False, null=False)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)





# class ending_balance_categories(models.Model):
#     ending_balance_category = models.CharField(max_length=100, blank=False, null = False)
#     def __str__(self):
#         return self.ending_balance_category
#
#
# class ending_balances(models.Model):
#     ending_balance_category = models.ForeignKey(ending_balance_categories, on_delete=models.PROTECT ,related_name = '+')
#     ending_balance_value = models.FloatField()
#     year = models.IntegerField(blank=True, null=True)
#     organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
#     report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
#     comments = models.TextField(blank=True, null=True)
#     history = HistoricalRecords()
class summary_report_status(models.Model):

    STATUS = (
        ("With user", "With user"),
        ("With WSDOT", "With WSDOT"),
        ("Complete", "Complete")
    )

    year = models.IntegerField()
    organization = models.ForeignKey(organization, on_delete=models.PROTECT)
    cover_sheet_status = models.CharField(default="With user", max_length=80, choices=STATUS)
    cover_sheet_submitted_for_review = models.BooleanField(default=False)
    data_report_status = models.CharField(default="With user", max_length=80, choices=STATUS)
    data_report_submitted_for_review = models.BooleanField(default=False)
    history = HistoricalRecords()

    class Meta:
        unique_together = ('year', 'organization',)


class summary_organization_progress(models.Model):

    organization = models.OneToOneField(organization, on_delete=models.PROTECT)
    started = models.BooleanField(default=False)
    address_and_organization = models.BooleanField(default=False)
    organization_details = models.BooleanField(default=False)
    service_cover_sheet = models.BooleanField(default=False)
    confirm_service = models.BooleanField(default=False)
    transit_data = models.BooleanField(default=False)
    revenue = models.BooleanField(default=False)
    expenses = models.BooleanField(default=False)
    ending_balances = models.BooleanField(default=False)


class tax_rates(models.Model):
    governance_structure = models.CharField(max_length=50, blank=True, null=True)
    year_established = models.IntegerField(blank=True, null=True)
    tax_rate = models.DecimalField(decimal_places=1, max_digits=5, blank=True, null=True)
    last_tax_rate_increase = models.CharField(max_length=30, blank=True, null=True)
    organization = models.OneToOneField(organization, on_delete=models.PROTECT)
    tax_rate_note = models.TextField(blank=True, null=True, default="N/A")

    @property
    def tax_rate_description(self):
        """Returns the description of tax rate used in the cover sheet."""
        if self.tax_rate_note:
            return self.tax_rate_note

        return "{}% sales tax. Last updated: {}".format(self.tax_rate, self.last_tax_rate_increase)


class intercity_bus_lines(models.Model):
    intercity_bus_line = models.CharField(max_length=50, blank=True, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT)


class cover_sheet_review_notes(models.Model):
    NOTE_AREAS = (
        ("Address", "Address"),
        ("Organization", "Organization"),
        ("Service", "Service"),
    )

    NOTE_STATUS = (
        ("Open", "Open"),
        ("Closed", "Closed"),
        ("Waiting", "Waiting"),
    )

    year = models.IntegerField()
    summary_report_status = models.ForeignKey(summary_report_status, on_delete=models.PROTECT)
    note = models.TextField(blank=True, null=True)
    note_area = models.CharField(max_length=80, choices=NOTE_AREAS)
    note_field = models.CharField(max_length=80, blank=True, null=True)
    wsdot_note = models.BooleanField(default=True)
    parent_note = models.IntegerField(blank=True, null=True)
    note_status = models.CharField(max_length=50, choices=NOTE_STATUS, default="Open")
    custom_user = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            if self.parent_note:
                parent_note = cover_sheet_review_notes.objects.get(id=self.parent_note)
                if self.wsdot_note:
                    parent_note.note_status = "Open"
                else:
                    parent_note.note_status = "Waiting"
                parent_note.save()

        super(cover_sheet_review_notes, self).save(*args, **kwargs)


class tribal_reporter_permissions(models.Model):
    year = models.IntegerField()
    organization = models.ForeignKey(organization, on_delete=models.PROTECT)
    permission_to_publish_coversheet = models.BooleanField(default=False)
    permission_to_publish_ntd_data = models.BooleanField(default=False, verbose_name="Permission to publish NTD data")
    permission_to_publish_reported_data = models.BooleanField(default=False)

    class Meta:
        unique_together = ('year', 'organization',)

# class ending_balance_categories(models.Model):
#     ending_balance_category = models.CharField(max_length=100, blank=False, null = False)
#     def __str__(self):
#         return self.ending_balance_category
#
#
# class ending_balances(models.Model):
#     ending_balance_category = models.ForeignKey(ending_balance_categories, on_delete=models.PROTECT ,related_name = '+')
#     ending_balance_value = models.FloatField()
#     year = models.IntegerField(blank=True, null=True)
#     organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
#     report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
#     comments = models.TextField(blank=True, null=True)
#     history = HistoricalRecords()






