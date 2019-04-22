from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser, BaseUserManager  ## A new class is imported. ##
from django.db import models
from django.db.models.functions import datetime
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from localflavor.us.models import USStateField, USZipCodeField
from phonenumber_field.modelfields import PhoneNumberField


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
    def __str__(self):
        return self.name

    name = models.CharField(max_length=80, blank=True)
    address_line_1 = models.CharField(max_length=50, blank=True)
    address_line_2 = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)
    vanshare_program = models.BooleanField(blank=True, null=True)


class profile(models.Model):
    custom_user = models.OneToOneField(get_user_model(), on_delete=models.PROTECT)
    profile_submitted = models.BooleanField(default=False)
    profile_complete = models.BooleanField(default=False)
    telephone_number = PhoneNumberField(blank=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT, blank=True, null=True)
    address_line_1 = models.CharField(max_length=50, blank=True)
    address_line_2 = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = USZipCodeField(blank=True)
    reports_on = models.ManyToManyField(ReportType, blank=True, null=True)


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
    report_due_date = models.DateField()
    report_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    report_by = models.ForeignKey(custom_user, on_delete=models.PROTECT, blank=True, null=True)
    organization = models.ForeignKey(organization, on_delete=models.PROTECT)
    vanshare_groups_in_operation = models.IntegerField(blank=True, null=True)
    vanshare_group_starts = models.IntegerField(blank=True, null=True)
    vanshare_group_folds = models.IntegerField(blank=True, null=True)
    vanshare_passenger_trips = models.IntegerField(blank=True, null=True)
    vanshare_miles_traveled = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=15)
    vanpool_groups_in_operation = models.IntegerField(blank=True, null=True)
    vanpool_group_starts = models.IntegerField(blank=True, null=True)
    vanpool_group_folds = models.IntegerField(blank=True, null=True)
    vans_available = models.IntegerField(blank=True, null=True)
    loaner_spare_vans_in_fleet = models.IntegerField(blank=True, null=True)
    vanpool_passenger_trips = models.IntegerField(blank=True, null=True)
    vanpool_miles_traveled = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=15)
    average_riders_per_van = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=15)
    average_round_trip_miles = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=15)

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

    def save(self, no_report_date=False, *args, **kwargs):

        if not no_report_date and self.report_date is None:
            self.report_date = datetime.datetime.now().date()
        super(vanpool_report, self).save(*args, **kwargs)

@receiver(post_save, sender=custom_user)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile.objects.create(custom_user=instance)


# @receiver(post_save, sender=custom_user)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()
