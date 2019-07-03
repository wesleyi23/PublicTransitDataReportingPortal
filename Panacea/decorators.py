from django.contrib.auth.decorators import user_passes_test
from django.conf import settings

def group_required(*group_names):
   """Requires user membership in at least one of the groups passed in."""

   def in_groups(current_user):
        if not settings.ENABLE_PERMISSIONS:
            return True
        if current_user.is_authenticated:
            if current_user.groups.filter(name__in=group_names).exists():
                return True
        return False

   return user_passes_test(in_groups)

