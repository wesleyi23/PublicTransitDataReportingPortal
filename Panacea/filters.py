from .models import vanpool_expansion_analysis
import django_filters


class VanpoolExpansionFilter(django_filters.FilterSet):
    class Meta:
        model = vanpool_expansion_analysis
        fields = ['vanpool_goal_met', 'expired', 'awarded_biennium']