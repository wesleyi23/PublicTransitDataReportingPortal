from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager  ## A new class is imported. ##
from django.db import models
from django.db.models.functions import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField
import datetime


# Create your models here.
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


# User authentication from tut located here:https://wsvincent.com/django-custom-user-model-tutorial/
class custom_user(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)  # changes email to unique and blank to false
    random_field = models.CharField(max_length=80, blank=True)

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


class organization(models.Model):
    AGENCY_CLASSIFICATIONS = (
        ("Urban", "Urban"),
        ("Small Urban", "Small Urban"),
        ("Rural", "Rural"),
    )

    CHOICES = (
        ('13-15', '13-15'),
        ('15-17', '15-17'),
        ('17-19', '17-19'),
        ('19-21', '19-21'),
        ('21-23', '21-23')
    )

    def __str__(self):
        return self.name

    #biennia = models.CharField(max_length=50, choices=CHOICES, blank=True, null=True)
    name = models.CharField(max_length=80, blank=True)
    address_line_1 = models.CharField(max_length=50, blank=True)
    address_line_2 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)
    classification = models.CharField(max_length=50, choices=AGENCY_CLASSIFICATIONS, blank=True, null=True)
    vanshare_program = models.BooleanField(blank=True, null=True)
    vanpool_expansion = models.BooleanField(blank=True, null=True)
    # this is kind of a hack and I hate it; on the other hand, it seems less complex than storing a list
    # TODO add to agency profile form
    in_jblm_area = models.BooleanField(blank=True, null=True)
    in_puget_sound_area = models.BooleanField(blank=True, null=True)


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
    reports_on = models.ManyToManyField(ReportType, blank=True)


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
    report_date = models.DateTimeField(default = None, null=True)
    updated_date = models.DateTimeField(auto_now=True, blank=True, null=True)
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
    average_riders_per_van = models.FloatField(blank=True, null=True)
    average_round_trip_miles = models.FloatField(blank=True, null=True)
    data_change_explanation = models.CharField(max_length=5000, blank=True, null=True)
    data_change_record = models.CharField(max_length=10000, blank=True, null=True)  # TODO change to JSONField when/if we hook up MySQL

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
    def report_due_date(self):
        month = self.report_month
        year = self.report_year + month // 12
        month = month % 12 + 1
        day = 1
        return datetime.date(year, month, day)

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


@receiver(post_save, sender=custom_user)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile.objects.create(custom_user=instance)


@receiver(post_save, sender=custom_user)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class vanpool_expansion_analysis(models.Model):
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


    organization = models.ForeignKey(organization, on_delete=models.PROTECT, related_name = '+')
    vanpools_in_service_at_time_of_award = models.IntegerField(blank=True, null=True)
    date_of_award = models.DateField(blank = True, null = True)
    expansion_vans_awarded = models.IntegerField(blank= True, null = True)
    latest_vehicle_acceptance = models.DateField(blank =True, null=True)
    extension_granted = models.BooleanField(blank = False, null = True)
    vanpool_goal_met = models.BooleanField(blank=False, null = True)
    expired = models.BooleanField(blank=False, null = True)
    notes = models.TextField(blank = False, null = True)
    awarded_biennium = models.CharField(max_length=50, choices=CHOICES, blank=True, null=True)
    expansion_goal = models.IntegerField(blank = True, null = True)
    deadline = models.DateField(blank = True, null = True)


    # going to need to add a loan thing here once I figure out what the story is


    @property
    def adjusted_service_goal(self):
        return int(self.vanpools_in_service_at_time_of_award + round(self.expansion_vans_awarded*.8, 0))




#TODO Change all the forms so we get good data, put various checks into the views page,


    @property
    # TODO should this be here or a function in utilities also we may want to rewrite this so it works no mater what date we put in
    def calculate_current_biennium(self):
        import datetime
        today = datetime.date.today()
        if today < datetime.date(2019, 6, 1):
            current_biennium = '17-19'
        # TODO you may want to simplify these as suggested by PyCharm
        elif today >= datetime.date(2019, 6, 1) and today < datetime.date(2021, 6, 1):
            current_biennium = '19-21'
        elif today >= datetime.date(2021, 6, 1) and today < datetime.date(2023, 6, 1):
            current_biennium = '21-23'
        elif today >= datetime.date(2023, 6, 1) and today < datetime.date(2025, 6, 1):
            current_biennium = '21-25'
        return current_biennium





