from .models import vanpool_expansion_analysis, vanpool_report
import django_filters


class VanpoolExpansionFilter(django_filters.FilterSet):
    class Meta:
        model = vanpool_expansion_analysis
        fields = ['vanpool_goal_met', 'expired', 'award_biennium']

    def __init__(self, *args, **kwargs):
        super(VanpoolExpansionFilter, self).__init__(*args, **kwargs)
        self.filters['vanpool_goal_met'].label = 'Service Expansion Goal Met'
        self.filters['expired'].label = 'Has the deadline passed?'
        self.filters['award_biennium'].label = "Select an awarded biennium"


class VanpoolReportFilter(django_filters.FilterSet):
    class Meta:
        model = vanpool_report
        fields = ['report_year']

    def __init__(self, *args, **kwargs):
        super(VanpoolReportFilter, self).__init__(*args, **kwargs)
        self.filters['report_year'].label = 'Please input a service year'