from .models import vanpool_expansion_analysis
import django_filters


class VanpoolExpansionFilter(django_filters.FilterSet):
    class Meta:
        model = vanpool_expansion_analysis
        fields = ['vanpool_goal_met', 'expired', 'awarded_biennium']

    def __init__(self, *args, **kwargs):
        super(VanpoolExpansionFilter, self).__init__(*args, **kwargs)
        self.filters['vanpool_goal_met'].label = 'Service Expansion Goal Met'
        self.filters['expired'].label = 'Has the deadline passed?'
        self.filters['awarded_biennium'].label = "Select an awarded biennium"