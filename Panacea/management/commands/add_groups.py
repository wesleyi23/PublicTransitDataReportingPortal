import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

# GROUPS = ['WSDOT_staff', 'vanpool_reporter', 'summary_reporter']
# MODELS = ['video', 'article', 'license', 'list', 'page', 'client']
# PERMISSIONS = ['view', ]  # For now only view permission by default for all, others include add, delete, change


def create_group(group_name, models, permissions):
    new_group, created = Group.objects.get_or_create(name=group_name)
    for model in models:
        model = model.lower()
        for permission in permissions:
            name = '{}_{}'.format(permission, model)
            print("Creating {}".format(name))

            try:
                model_add_perm = Permission.objects.get(codename=name)
            except Permission.DoesNotExist:
                logging.warning("Permission not found with name '{}'.".format(name))
                continue

            new_group.permissions.add(model_add_perm)


class Command(BaseCommand):
    help = 'Creates group permissions'

    def handle(self, *args, **options):
        # WSDOT Staff permissions
        group = 'WSDOT staff'
        models = ['custom_user', 'organization', 'profile', 'ReportType', 'vanpool_report']
        permissions = ['view', 'change', 'add', 'delete']
        create_group(group, models, permissions)

        # Vanpool reporter permissions
        group = 'Vanpool reporter'
        permissions = ['view', 'change', 'add', 'delete']
        models = ['custom_user', 'organization', 'profile', 'ReportType', 'vanpool_report']
        create_group(group, models, permissions)

        # Summary reporter permissions
        group = 'Summary reporter'
        permissions = ['view', 'change', 'add', 'delete']
        models = ['custom_user', 'organization', 'profile', 'ReportType']
        create_group(group, models, permissions)

        permissions = ['view', ]
        models = ['vanpool_report', ]
        create_group(group, models, permissions)

    print("Created default group and permissions.")