import datetime
import itertools

from django.db import transaction
from django.db.models import Sum, F, Q, ExpressionWrapper, FloatField
from django.forms import modelformset_factory
from django.http import Http404
from django.shortcuts import redirect

from Panacea.models import service_offered, revenue, transit_data, expense, fund_balance, revenue_source, \
    transit_metrics, expense_source, fund_balance_type, transit_mode, summary_organization_progress, organization

from Panacea.utilities import get_current_summary_report_year, get_all_data_steps_completed
from django import forms
from django.forms import modelformset_factory, BaseModelFormSet, ModelForm
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side



class StatewideReports:
    def __init__(self):
        self.REPORT_TYPES = ['investments', 'financial_expenses', 'operating_stats',  'revenues', 'financial_revenues', 'service_mode_tables']
    def get_current_report_years(self):
        current_year = get_current_summary_report_year()
        years = [current_year - 2, current_year - 1, current_year]
        return years
    def get_long_years(self):
        current_year = get_current_summary_report_year()
        years = [current_year-5, current_year-4, current_year-3, current_year - 2, current_year - 1, current_year]
        return years
    def get_current_report_year(self):
        current_year = get_current_summary_report_year()
        return current_year

class StatewideSixYearReportBuilder(StatewideReports):
    def __init__(self, report_type, big):
        super().__init__()
        self.report_type = report_type
        self.big = big
        self.years = self.get_long_years()
        self.transits = 6
        self.operational_dic = {'Revenue Vehicle Hours by Service Mode': 1, 'Revenue Vehicle Miles by Service Mode': 2, 'Passenger Trips by Service Mode':5, 'Farebox Revenues by Service Mode': 10,
                           'Operating Expenses by Service Mode': 9, 'Operating Cost per Passenger Trip': [9, 5], 'Operating Cost per Revenue Vehicle Hour': [9, 1],
                           'Passenger Trips per Revenue Vehicle Hour': [5,1], 'Passenger Trips per Revenue Vehicle Miles': [5,2], 'Revenue Vehicle Hours per Employee': [1,8],
                           'Farebox Recovery Ratio': [10, 9]}
        self.investment_types = ['Local', 'State', 'Federal', 'Other']
        self.modes = ['Fixed Route', 'Route Deviated', 'Demand Response', 'Vanpool', 'Commuter Rail', 'Light Rail']

    def pull_data(self):
        if self.report_type == 'operating_stats':
            return transit_data

    def generate_percent_change(self, data_list):
        '''function for adding percent change to summary tables'''
        try:
            percent_change = ((data_list[-1] - data_list[-2]) / data_list[-2]) * 100
        except ZeroDivisionError:
            if data_list[-1] == data_list[-2] == 0:
                percent_change = '-'
            else:
                percent_change = 100.00
        return percent_change

    def turn_into_list_of_lists_for_modes(self, iterables, report_data):
        list_of_lists =[]
        for mode in iterables:
            year_list = []
            year_list.append(mode)
            for year in self.get_long_years():
                value = report_data.filter(transit_mode__rollup_mode = mode, year = year).values_list('reported_value__sum', flat=True)[0]
                year_list.append(value)
            percent_change = self.generate_percent_change(year_list)
            year_list = year_list + [percent_change]
            list_of_lists.append(year_list)
        return list_of_lists

    def turn_into_list(self, ls):
        result_list = []
        for i in ls:
            result_list.append(i['reported_value'])
        return result_list


    def percent_of_total(self, data_list):
        for k in data_list[:-1]:
            percent_of_total = k[-1]/data_list[-1][-1]
            k.append(percent_of_total)
        return data_list


    def build_tables(self):
        if self.report_type =='operating_stats':
            data_list = []
            heading_list = []
            for table_name in self.operational_dic.items():
                if isinstance(table_name[1], list):
                    report_data = transit_data.objects.filter(organization__summary_organization_classifications=6,
                                                     transit_metric_id__in=table_name[1],year__in= self.years,
                                                     reported_value__isnull=False).values('transit_mode__rollup_mode','year').annotate(denominator=Sum('reported_value', filter = Q(transit_metric_id=table_name[1][0])), numerator = Sum('reported_value', filter=Q(transit_metric_id=table_name[1][1])))
                    report_data = report_data.annotate(reported_value__sum = ExpressionWrapper(F('denominator')*1.0/F('numerator'), output_field = FloatField()))
                else:
                    report_data = self.pull_data().objects.filter(organization__summary_organization_classifications=self.transits,
                                                    transit_metric_id=table_name[1], year__in=self.years,
                                                    reported_value__isnull=False).values('transit_mode__rollup_mode',
                                                                                         'year').annotate(Sum('reported_value')).order_by('year')
                report_data = self.turn_into_list_of_lists_for_modes(self.modes, report_data)
                data_list.append(report_data)
                heading = [table_name[0]] + self.years + ['One Year Change (%)']
                heading_list.append(heading)
        elif self.report_type == 'revenues':
            pass
        elif self.report_type == 'investments' and self.big is not 'sound':
            heading_list = ['Capital Investment Source', self.years]
            local_cap = ['Local Capital Investment'] + list(expense.objects.filter(organization__summary_organization_classifications=6, expense_source_id = 1, year__in = self.years, reported_value__isnull=False).values('year').annotate(reported_value = Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
            state_cap = ['State Capital Investment'] + list(revenue.objects.filter(organization__summary_organization_classifications = 6, revenue_source__government_type = 'State', revenue_source__funding_type = 'Capital', year__in = self.years, reported_value__isnull=False).exclude(revenue_source_id =96).values('year').annotate(reported_value = Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
            federal_cap = ['Federal Capital Investment'] + list(revenue.objects.filter(organization__summary_organization_classifications = 6, revenue_source__government_type = 'Federal', revenue_source__funding_type = 'Capital', year__in = self.years, reported_value__isnull=False).values('year').annotate(reported_value = Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
            other_cap = ['Other Capital Investment'] + list(expense.objects.filter(organization__summary_organization_classifications=6, expense_source_id__in = [2,4,5], year__in = self.years, reported_value__isnull=False).values('year').annotate(reported_value = Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
        elif self.report_type == 'investments' and self.big == 'sound':
            heading_list = ['Capital Investment Source', self.years]
            local_cap = ['Local Capital Investment'] + list(expense.objects.filter(organization__summary_organization_classifications=6, expense_source_id=1,year__in=self.years, reported_value__isnull=False).exclude(organization_id__in= [15,33]).values('year').annotate(reported_value=Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
            state_cap = ['State Capital Investment'] + list(revenue.objects.filter(organization__summary_organization_classifications=6,revenue_source__government_type='State', revenue_source__funding_type='Capital',year__in=self.years, reported_value__isnull=False).exclude(revenue_source_id=96, organization_id__in = [15,33]).values('year').annotate(reported_value=Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
            federal_cap = ['Federal Capital Investment'] + list(revenue.objects.filter(organization__summary_organization_classifications=6,revenue_source__government_type='Federal',revenue_source__funding_type='Capital', year__in=self.years,reported_value__isnull=False).exclude(organization_id__in= [15,33]).values('year').annotate(reported_value=Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
            other_cap = ['Other Capital Investment'] + list(expense.objects.filter(organization__summary_organization_classifications=6,expense_source_id__in=[2, 4, 5], year__in=self.years,reported_value__isnull=False).exclude(organization_id__in= [15,33]).values('year').annotate(reported_value=Sum('reported_value')).values_list('reported_value', flat=True).order_by('year'))
        total_list = [local_cap[1:], state_cap[1:], federal_cap[1:], other_cap[1:]]
        total = [sum(i) for i in zip(*total_list)]
        total = ['Total Investment'] + total
        data_list = [local_cap, state_cap, federal_cap, other_cap, total]
        return heading_list, data_list




class SummaryBuilder:
    def __init__(self):
        self.REPORT_TYPES = ['transit_data', 'revenue', 'expense', 'fund_balance']

class SummaryBuilderReportType(SummaryBuilder):

    def __init__(self, report_type):
        super().__init__()
        self.report_type = report_type

    def get_model(self):
        '''returns the appropriate model for the given report type'''
        if self.report_type == "revenue":
            return revenue
        elif self.report_type == "transit_data":
            return transit_data
        elif self.report_type == "expense":
            return expense
        elif self.report_type == "fund_balance":
            return fund_balance
        else:
            raise Http404("Report type does not exist. -4")

    def get_model_data(self):
        '''returns the appropriate model for the given report type'''
        if self.report_type == "revenue":
            return revenue.objects.filter(revenue_source__inactive_flag=False)
        elif self.report_type == "transit_data":
            return transit_data.objects
        elif self.report_type == "expense":
            return expense.objects
        elif self.report_type == "fund_balance":
            return fund_balance.objects
        else:
            raise Http404("Report type does not exist. -4")

    def get_metric_model(self):
        '''returns the appropriate metric model for the given report type'''
        if self.report_type == "revenue":
            return revenue_source
        elif self.report_type == "transit_data":
            return transit_metrics
        elif self.report_type == "expense":
            return expense_source
        elif self.report_type == "fund_balance":
            return fund_balance_type
        else:
            raise Http404("Report type does not exist. -5")

    def get_metric_model_data(self):
        '''returns the appropriate metric model for the given report type'''
        if self.report_type == "revenue":
            return revenue_source.objects.filter(inactive_flag=False)
        elif self.report_type == "transit_data":
            return transit_metrics.objects
        elif self.report_type == "expense":
            return expense_source.objects
        elif self.report_type == "fund_balance":
            return fund_balance_type.objects
        else:
            raise Http404("Report type does not exist. -5")

    def get_metric_model_name(self):
        '''Returns the metric model as a string.'''
        if self.report_type == "revenue":
            return 'revenue_source'
        elif self.report_type == "transit_data":
            return 'transit_metric'
        elif self.report_type == "expense":
            return 'expense_source'
        elif self.report_type == "fund_balance":
            return 'fund_balance_type'
        else:
            raise Http404("Report type does not exist. -6")

    def get_metric_id_field_name(self):
        '''Returns the name of the field name of the id field in the metric model as a string.'''
        if self.report_type == "transit_data":
            return 'transit_metric_id'
        else:
            metric_model = self.get_metric_model()
            return metric_model.__name__ + '_id'


class SummaryDataEntryBuilder(SummaryBuilderReportType):
    '''This class constructs all of the forms needed to collect summary data'''

    def __init__(self, report_type, target_organization, form_filter_1=None, form_filter_2=None):
        super().__init__(report_type)

        # self.report_type = report_type  # reports can be about revenue, transit data, expenses, and ending fund balances
        self.target_organization = target_organization  # the org submitting a report
        self.year = get_current_summary_report_year()  # TODO this function needs to be updated
        self.form_filter_1 = form_filter_1  # Forms can be filtered by the selectors at the top of the page for example reporting based on direct operated, fixed route transit
        self.form_filter_2 = form_filter_2
        # These control how the form moves to the next form
        self.max_form_increment = 0 #if the max increment is meet it will move to the next report type, otherwise it will go to the next set of filters
        self.current_increment = 0

        self.nav_filter_count, self.nav_filters = self.get_header_navigation()
        self.set_default_form_filters()  # sets the starting filters for the form
        self.set_max_form_increment()
        self.set_current_increment()

    def set_default_form_filters(self):
        if self.form_filter_1 is not None:
            pass
        else:
            # TODO create ordering for metric types
            if self.report_type == "revenue":
                self.form_filter_1 = self.nav_filters[0][0]
                self.form_filter_2 = self.nav_filters[0][1]
            elif self.report_type == "transit_data":
                # TODO Make this into something that makes more sense
                self.form_filter_1 = service_offered.objects.filter(organization=self.target_organization).order_by('transit_mode__name').values_list('transit_mode__name').first()[0]
                self.form_filter_2 = service_offered.objects.filter(organization=self.target_organization).order_by('transit_mode__name').values_list('administration_of_mode').first()[0]
                # self.form_filter_1 = self.get_model().objects.filter(organization=self.target_organization).order_by(
                #     'transit_mode__name').values_list('transit_mode__name').first()[0]
                # self.form_filter_2 = self.get_model().objects.filter(organization=self.target_organization).order_by(
                #     'administration_of_mode').values_list('administration_of_mode').first()[0]
            elif self.report_type in ["expense", "fund_balance"]:
                self.form_filter_1 = None
                self.form_filter_2 = None
            else:
                raise Http404("Report type does not exist. -1")

    def set_max_form_increment(self):
        '''returns the appropriate model for the given report type'''
        # if self.report_type == "revenue":
        #     self.max_form_increment = 7
        # elif self.report_type == "transit_data":
        #     self.max_form_increment = service_offered.objects.filter(organization=self.target_organization).count()
        # elif self.report_type == "expense":
        #     self.max_form_increment = 1
        # elif self.report_type == "fund_balance":
        #     self.max_form_increment = 1
        # else:
        #     raise Http404("Report type does not exist. -2")

        if isinstance(self.nav_filters, list):
            self.max_form_increment = len(self.nav_filters)
        else:
            self.max_form_increment = 1

    def set_current_increment(self):
        '''returns the appropriate model for the given report type'''
        if self.report_type == "revenue":
            self.current_increment = self.nav_filters.index([self.form_filter_1, self.form_filter_2]) + 1
        elif self.report_type == "transit_data":
            self.current_increment = self.nav_filters.index([self.form_filter_1, self.form_filter_2]) + 1
        elif self.report_type == "expense":
            self.current_increment = 1
        elif self.report_type == "fund_balance":
            self.current_increment = 1
        else:
            raise Http404("Report type does not exist. -3")

    def get_all_metric_ids(self):
        '''Returns a distinct list of all metric ids that are needed given the agency classification, if applicable.'''
        classification = self.target_organization.summary_organization_classifications
        if self.report_type in ['transit_data', 'revenue', ]:
            metric_ids = list(
                self.get_metric_model_data().filter(agency_classification=classification).values_list('id',
                                                                                                      flat=True).distinct())
        elif self.report_type in ['fund_balance', 'expense', ]:
            metric_ids = list(self.get_metric_model_data().values_list('id', flat=True).distinct())
        else:
            raise Http404
        return metric_ids

    def get_create_metric_dictionary(self, metric):
        '''Used to create a new empty instance of a report metric. So an empty form may be displayed'''
        create_dictionary = {}
        if self.report_type in ['transit_data', ]:
            create_dictionary = {'year': metric[1],
                                 'organization': self.target_organization,
                                 'transit_mode': transit_mode.objects.get(name=self.form_filter_1),
                                 'administration_of_mode': self.form_filter_2,
                                 self.get_metric_id_field_name(): metric[0],
                                 'reported_value': None,
                                 }
        elif self.report_type in ['revenue', 'expense', 'fund_balance', ]:
            create_dictionary = {'year': metric[1],
                                 'organization': self.target_organization,
                                 self.get_metric_id_field_name(): metric[0],
                                 'reported_value': None,
                                 }
        else:
            raise Http404
        return create_dictionary

    def get_or_create_all_form_metrics(self):
        '''Gets all reported form metrics applicable to the form type, organization, and year.  If the metric has not been reported it creates it.'''
        model = self.get_model_data()
        if self.report_type == "transit_data":
            report_model = model.filter(transit_mode__name=self.form_filter_1,
                                        administration_of_mode=self.form_filter_2)
        else:
            report_model = model
        field_id = self.get_metric_id_field_name()

        current_report_metric_ids = list(report_model.filter(organization=self.target_organization,
                                                             year__gte=self.year - 2).values_list(field_id,
                                                                                                  'year').distinct())
        all_report_metric_ids = self.get_all_metric_ids()
        all_metric_ids_and_years = list(
            itertools.product(all_report_metric_ids, [self.year, self.year - 1, self.year - 2]))
        if len(current_report_metric_ids) != len(all_metric_ids_and_years):

            all_metric_ids_and_years = set(map(tuple, all_metric_ids_and_years))
            current_report_metric_ids = set(map(tuple, current_report_metric_ids))
            missing_metrics = list(all_metric_ids_and_years - current_report_metric_ids)
            # missing_metrics = all_metric_ids_and_years.symmetric_difference(current_report_metric_ids)
            # TODO there are some metrics that are currently filtered out that orgs previously reported on. How do we want to deal with these?
            if len(missing_metrics) > 0:
                with transaction.atomic():
                    for m in missing_metrics:
                        model.create(**self.get_create_metric_dictionary(m))

        form_metrics = model.filter(organization=self.target_organization).order_by(self.get_metric_id_field_name() + '__name')
        return form_metrics

    def get_widgets(self):
        '''Used to build widgets dynamically based on form type.'''

        if self.report_type == 'transit_data':
            widget_attrs = {'class': 'form-control validate-field', 'autocomplete': "off"}
        else:
            widget_attrs = {'class': 'form-control grand-total-sum validate-field', 'onchange': 'findTotal_wrapper();', 'autocomplete': "off"}

        widgets = {'id': forms.NumberInput(),
                   self.get_metric_model_name(): forms.Select(),
                   'year': forms.NumberInput(),
                   'reported_value': forms.TextInput(attrs=widget_attrs),
                   'comments': forms.Textarea(attrs={'class': 'form-control comment-field', "rows": 3})
                   }
        return widgets

    def create_model_formset_factory(self):
        '''Creates a fromset factory based on the information contained in the class information'''
        my_formset_factory = modelformset_factory(self.get_model(), form=ModelForm, formfield_callback=None,
                                                  formset=BaseModelFormSet, extra=0, can_delete=False,
                                                  can_order=False, max_num=None,
                                                  fields=["id", self.get_metric_model_name(), "year", "reported_value",
                                                          "comments"],
                                                  exclude=None,
                                                  widgets=self.get_widgets(),
                                                  validate_max=False, localized_fields=None,
                                                  labels=None, help_texts=None, error_messages=None,
                                                  min_num=None, validate_min=False, field_classes=None)

        return my_formset_factory

    def get_formset_query_dict(self):
        '''Builds a dynamic dictionary used for querying the aproriate metrics giving the filter criteria and organization classification'''
        if self.report_type in ['transit_data', ]:

            query_dict = {'transit_mode__name': self.form_filter_1,
                          'administration_of_mode': self.form_filter_2,
                          'transit_metric__agency_classification': self.target_organization.summary_organization_classifications
                          }
        elif self.report_type in ['revenue', ]:
            query_dict = {'revenue_source__government_type': self.form_filter_1,
                          'revenue_source__funding_type': self.form_filter_2,
                          'revenue_source__agency_classification': self.target_organization.summary_organization_classifications}
        elif self.report_type in ['expense', ]:
            query_dict = {'expense_source__agency_classification': self.target_organization.summary_organization_classifications}
        elif self.report_type in ['fund_balance', ]:
            query_dict = {'fund_balance_type__agency_classification': self.target_organization.summary_organization_classifications}
        else:
            raise Http404
        return query_dict

    def get_form_queryset(self):
        form_querysets = self.get_or_create_all_form_metrics()
        form_querysets = form_querysets.filter(**self.get_formset_query_dict())
        return form_querysets

    def get_formsets_labels_masking_class_and_help_text(self):
        '''Builds formsets by year with labels and masking classes'''
        my_formset_factory = self.create_model_formset_factory()
        form_querysets = self.get_form_queryset()

        formsets = {}
        i = 0
        for year_x in ['this_year', 'previous_year', 'two_years_ago']:
            formsets[year_x] = my_formset_factory(
                queryset=form_querysets.filter(year=self.year - i),
                prefix=year_x)
            i += 1
        formset_labels = form_querysets.filter(year=self.year).values_list(
            self.get_metric_model_name() + "__name", flat=True)
        help_text = form_querysets.filter(year=self.year).values_list(
            self.get_metric_model_name() + "__help_text", flat=True)
        if self.report_type != "transit_data":
            masking_class = ['Money'] * len(formset_labels)
        else:
            masking_class = form_querysets.filter(year=self.year).values_list(
                self.get_metric_model_name() + "__form_masking_class", flat=True)

        return formsets, formset_labels, masking_class, help_text

    def get_other_measure_totals(self):
        '''Gets totals from that need to be aggrigated on the page but are not presented due to the filters on the form.'''
        if self.report_type == 'transit_data':
            return None

        total_not_this_form = {}
        if self.get_formset_query_dict() == {}:
            for year_x in ['this_year', 'previous_year', 'two_years_ago']:
                total_not_this_form[year_x] = {'reported_value__sum': 0}
        else:
            report_model_data = self.get_model_data()
            total_not_this_form_queryset = report_model_data.filter(organization=self.target_organization).exclude(
                **self.get_formset_query_dict())
            i = 0
            for year_x in ['this_year', 'previous_year', 'two_years_ago']:
                total_not_this_form[year_x] = total_not_this_form_queryset.filter(year=self.year - i).aggregate(
                    Sum('reported_value'))
                if total_not_this_form[year_x]['reported_value__sum'] == None:
                    total_not_this_form[year_x]['reported_value__sum'] = 0
                i += 1

        return total_not_this_form

    def get_header_navigation(self):
        '''gets the data needed to build header navigation for filters'''
        if self.report_type in ['transit_data', ]:
            filter_count = 2
            my_services_offered = service_offered.objects.filter(organization=self.target_organization).order_by(
                'transit_mode__name')
            filters = []
            for service in my_services_offered:
                filters.append([service.transit_mode.name, service.administration_of_mode])
        elif self.report_type in ['revenue', ]:
            filter_count = 2
            revenues = revenue_source.objects.filter(
                agency_classification=self.target_organization.summary_organization_classifications).values(
                'government_type', 'funding_type').distinct()

            filters = []
            for source in revenues:
                filters.append([source['government_type'], source['funding_type']])

            if len(filters) > 1:
                revenue_list_order_type = ['Operating', 'Capital', 'Other']
                revenue_list_order_gov = ['Local', 'State', 'Federal', 'Other']
                filters.sort(key=lambda x: revenue_list_order_type.index(x[1]))
                filters.sort(key=lambda x: revenue_list_order_gov.index(x[0]))


        elif self.report_type in ['expense', 'fund_balance', ]:
            filter_count = 0
            if self.report_type == 'expense':
                filters = 'Expenses'
            elif self.report_type == 'fund_balance':
                filters = "Ending fund balances"
        else:
            raise Http404

        return filter_count, filters

    def save_with_post_data(self, post_data):
        my_formset_factory = self.create_model_formset_factory()
        query_sets = self.get_form_queryset()
        i = 0
        for year_x in ['this_year', 'previous_year', 'two_years_ago']:
            query = query_sets.filter(year=self.year - i).order_by(
                self.get_metric_id_field_name())
            formset = my_formset_factory(post_data, queryset=query_sets.filter(year=self.year - i).order_by(
                self.get_metric_id_field_name()), prefix=year_x)
            for form in formset:
                if form.is_valid():
                    form.save()
                else:
                    print(form.errors)

            i += 1

    def go_to_next_form(self, save_only=False):
        if save_only:
            return redirect('summary_reporting_filters', self.report_type, self.form_filter_1, self.form_filter_2)
        next_increment = self.current_increment + 1
        if next_increment > self.max_form_increment:
            org_progress = summary_organization_progress.objects.get(organization=self.target_organization)
            if self.report_type == 'fund_balance':
                org_progress.ending_balances = True
                org_progress.save()
                if get_all_data_steps_completed(self.target_organization.id):
                    return redirect('submit_data')
                else:
                    return redirect('you_skipped_a_step')
            else:
                if self.report_type == "revenue":
                    org_progress.revenue = True
                    org_progress.save()
                elif self.report_type == "transit_data":
                    org_progress.transit_data = True
                    org_progress.save()
                elif self.report_type == "expense":
                    org_progress.expenses = True
                    org_progress.save()
                elif self.report_type == "fund_balance":
                    raise Http404("Report type does not exist. -7a")
                else:
                    raise Http404("Report type does not exist. -7b")

                new_report_type = self.REPORT_TYPES[self.REPORT_TYPES.index(self.report_type) + 1]
                return redirect('summary_reporting_type', new_report_type)
        else:
            self.form_filter_1 = self.nav_filters[self.current_increment][0]
            self.form_filter_2 = self.nav_filters[self.current_increment][1]
            return redirect('summary_reporting_filters', self.report_type, self.form_filter_1, self.form_filter_2)

    def get_next_builder(self):
        self.current_increment = self.current_increment + 1
        if self.current_increment > self.max_form_increment:
            try:
                new_report_type = self.REPORT_TYPES[self.REPORT_TYPES.index(self.report_type) + 1]
                new_form_filter_1 = None
                new_form_filter_2 = None
            except:
                return False
        else:
            new_report_type = self.report_type
            new_form_filter_1 = self.nav_filters[self.current_increment - 1][0]
            new_form_filter_2 = self.nav_filters[self.current_increment - 1][1]

        new_builder = SummaryDataEntryBuilder(new_report_type, self.target_organization, new_form_filter_1, new_form_filter_2)

        return new_builder


class SummaryDataEntryTemplateData:
    '''Simple class that uses the SummaryDataEntryBuilder to create data needed in the template'''

    def __init__(self, data_entry_factory, report_type):
        self.formsets, self.formset_labels, self.masking_class, self.help_text = data_entry_factory.get_formsets_labels_masking_class_and_help_text()
        self.report_type = report_type
        self.year = data_entry_factory.year
        self.form_filter_1 = data_entry_factory.form_filter_1
        self.form_filter_2 = data_entry_factory.form_filter_2
        self.other_totals = data_entry_factory.get_other_measure_totals()
        self.masking_types = []
        self.nav_filter_count = data_entry_factory.nav_filter_count
        self.nav_filters = data_entry_factory.nav_filters

        if data_entry_factory.report_type == "transit_data":
            self.show_totals = False
        else:
            self.show_totals = True

        if len(self.formset_labels) == 0:
            self.no_reports = True
        else:
            self.no_reports = False


class ConfigurationBuilder(SummaryBuilderReportType):

    def __init__(self, report_type, help_text=None):
        super().__init__(report_type)
        self.REPORT_TYPES = ['organization', 'transit_data', 'revenue', 'expense', 'fund_balance']
        self.help_text = help_text

        if self.help_text is None:
            self.primary_field_name, self.other_fields_list = self.get_model_fields()
        else:
            self.primary_field_name = "help_text"
            self.other_fields_list = []

    def get_model(self):
        if self.report_type == 'organization':
            return organization
        else:
            return super(ConfigurationBuilder, self).get_model()

    def get_model_data(self):
        if self.report_type == 'organization':
            return organization.objects
        elif self.report_type == "revenue":
            return revenue.objects.filter()
        elif self.report_type == "transit_data":
            return transit_data.objects
        elif self.report_type == "expense":
            return expense.objects
        elif self.report_type == "fund_balance":
            return fund_balance.objects
        else:
            raise Http404("Report type does not exist. -4")

    def get_metric_model(self):
        if self.report_type == 'organization':
            return organization
        else:
            return super(ConfigurationBuilder, self).get_metric_model()

    def get_metric_model_data(self):
        if self.report_type == 'organization':
            return organization.objects
        elif self.report_type == "revenue":
            return revenue_source.objects
        elif self.report_type == "transit_data":
            return transit_metrics.objects
        elif self.report_type == "expense":
            return expense_source.objects
        elif self.report_type == "fund_balance":
            return fund_balance_type.objects
        else:
            raise Http404("Report type does not exist. -5")

    def get_model_fields(self):
        '''returns the appropriate model for the given report type'''
        if self.report_type == "revenue":
            primary_field_name = 'agency_classification'
            other_fields_list = ['funding_type', 'government_type', 'inactive_flag']
            return primary_field_name, other_fields_list
        elif self.report_type == "transit_data":
            primary_field_name = 'agency_classification'
            other_fields_list = []
            return primary_field_name, other_fields_list
        # TODO add in expense and fund balance
        elif self.report_type == "expense":
            primary_field_name = 'agency_classification'
            other_fields_list = []
            return primary_field_name, other_fields_list
        elif self.report_type == "fund_balance":
            primary_field_name = 'agency_classification'
            other_fields_list = []
            return primary_field_name, other_fields_list
        elif self.report_type == "organization":
            primary_field_name = 'summary_organization_classifications'
            other_fields_list = []
            return primary_field_name, other_fields_list
        else:
            raise Http404("Report type does not exist. -4a")

    def get_data_relationship_one_2_one(self):
        if self.report_type in ['organization']:
            return True
        elif self.report_type in ['revenue', 'transit_data', 'expense', 'fund_balance']:
            return False
        else:
            return Http404("Report type does not exist. -4b")

    def create_model_formset_factory(self):
        '''Creates a fromset factory based on the information contained in the class information'''
        my_formset_factory = modelformset_factory(self.get_metric_model(), form=ModelForm, formfield_callback=None,
                                                  formset=BaseModelFormSet, extra=0, can_delete=False,
                                                  can_order=False, max_num=None,
                                                  fields=['id', "name", self.primary_field_name] + self.other_fields_list,
                                                  exclude=None,
                                                  widgets=self.get_widgets(),
                                                  validate_max=False, localized_fields=None,
                                                  labels=None, help_texts=None, error_messages=None,
                                                  min_num=None, validate_min=False, field_classes=None)

        return my_formset_factory

    def get_query_set(self):
        query_set = self.get_metric_model_data().order_by('name').all()
        return query_set

    def get_widgets(self):
        '''widgets'''
        if self.help_text is not None:
            widgets = {'id': forms.NumberInput(),
                       'name': forms.TextInput(attrs={'class': 'form-control AJAX_instant_submit',
                                                      'data-form-name': "summary_configure"}),
                       self.primary_field_name: forms.Textarea(attrs={'class': 'form-control AJAX_instant_submit',
                                                                      'data-form-name': "summary_configure",
                                                                      'rows': 2})}
            return widgets

        if self.get_data_relationship_one_2_one():
            widgets = {'id': forms.NumberInput(),
                       'name': forms.TextInput(attrs={'class': 'form-control AJAX_instant_submit',
                                                      'data-form-name': "summary_configure"}),
                       self.primary_field_name: forms.Select(attrs={'class': 'form-control AJAX_instant_submit',
                                                                    'data-form-name': "summary_configure"})}

        else:
            widgets = {'name': forms.TextInput(attrs={'class': 'form-control'}),
                       self.primary_field_name: forms.CheckboxSelectMultiple(
                           attrs={'class': 'form-check-inline no-bullet AJAX_instant_submit',
                                  'data-form-name': "summary_configure"})}

        if len(self.other_fields_list) > 0:
            for field in self.other_fields_list:
                widgets[field] = forms.Select(attrs={'class': 'form-control AJAX_instant_submit',
                                                     'data-form-name': "summary_configure"})

        return widgets

    def get_form_set(self, **kwargs):
        my_formset_factory = self.create_model_formset_factory()
        my_formset = my_formset_factory(queryset=self.get_query_set(), **kwargs)
        return my_formset


class ExportReport(SummaryBuilder):
    def __init__(self, target_organization):
        super().__init__()
        self.target_organization = target_organization
        self.report_type_sub_report_list = {}
        self.gather_report_data()

    def gather_report_data(self):
        next_builder = SummaryDataEntryBuilder(report_type=self.REPORT_TYPES[0], target_organization=self.target_organization)
        while next_builder:
            t, nav_headers = next_builder.get_header_navigation()
            if isinstance(nav_headers, list):
                nav_headers = nav_headers[next_builder.current_increment-1]
            data = ExportReport_Data(nav_headers,
                                     next_builder.get_form_queryset())
            if next_builder.report_type not in self.report_type_sub_report_list:
                new_report_type = ExportReport_ReportType(next_builder.report_type)
                new_report_type.append_export_report_data(data)
                self.report_type_sub_report_list[next_builder.report_type] = new_report_type
            else:
                self.report_type_sub_report_list[next_builder.report_type].append_export_report_data(data)
            next_builder = next_builder.get_next_builder()

    def generate_report(self, file_save_os=False):
        year = get_current_summary_report_year()
        wb = Workbook()
        ws = wb.active
        bd = Side(style='medium', color="000000")
        ws.title = "SummaryReportData"
        ws.column_dimensions['A'].width = 47
        ws.column_dimensions['B'].width = 10
        ws.column_dimensions['C'].width = 10
        ws.column_dimensions['D'].width = 10

        ws.append([self.target_organization.name])
        style_cell = ws.cell(row=ws.max_row, column=1)
        style_cell.font = Font(size=20, bold=True)
        ws.append(["Summary of Public Transportation Report data export run: {}".format(datetime.datetime.now())])
        style_cell = ws.cell(row=ws.max_row, column=1)
        style_cell.font = Font(italic=True)
        ws.append([])
        for report_type in self.report_type_sub_report_list.values():

            for data in report_type.export_report_data_list:
                i = 0
                ws.append(["{} - {}".format(report_type.pretty_report_type, data.nav_headers)])
                style_cell = ws.cell(row=ws.max_row, column=1)
                style_cell.font = Font(bold=True)
                style_cell.border = Border(bottom=bd)
                ws.cell(row=ws.max_row, column=2).border = Border(bottom=bd)
                ws.cell(row=ws.max_row, column=3).border = Border(bottom=bd)
                ws.cell(row=ws.max_row, column=4).border = Border(bottom=bd)

                col_data = {}
                ws.append(['',  year - 2, year - 1, year])
                for year_x in ['this_year', 'previous_year', 'two_years_ago']:
                    col_data[year_x] = list(data.query_set.filter(year=year - i).values_list('reported_value', flat=True))
                    i = i + 1
                col_labels = data.query_set.filter(year=year).values_list(
                    report_type.get_metric_model_name() + "__name", flat=True)
                for k, col in enumerate(col_labels):
                    ws.append([col, col_data['two_years_ago'][k], col_data['previous_year'][k], col_data['this_year'][k]])
                ws.append([])
        if file_save_os:
            wb.save(filename="text.xlsx")
        else:
            return wb


class ExportReport_ReportType(SummaryBuilderReportType):
    def __init__(self, report_type):
        super().__init__(report_type)
        self.export_report_data_list = []
        self.pretty_report_type = self.get_pretty_report_type()

    def append_export_report_data(self, data):
        self.export_report_data_list.append(data)

    def get_pretty_report_type(self):
        if self.report_type == "revenue":
            return 'Revenue'
        elif self.report_type == "transit_data":
            return 'Transit Data'
        elif self.report_type == "expense":
            return 'Expenses'
        elif self.report_type == "fund_balance":
            return 'Fund balances'
        else:
            raise Http404("Report type does not exist. -6")


class ExportReport_Data():
    def __init__(self, nav_headers, query_set):
        if isinstance(nav_headers, list):
            self.nav_headers = ' '.join([str(elem) for elem in nav_headers])
        else:
            self.nav_headers = nav_headers
        self.query_set = query_set.filter(year__gte=get_current_summary_report_year()-3)



# what i need is a set of dictionaries/querysets in the correct order
# I need the following special capabilities:
# 1) create special rows/tables based on the type of data that is being queried
# 2) dynamically create headings based on the data that is pulled
# 3) preserve spacing and indentation norms
# 4) follow a particular order of display that can change based on report type, separate for ferry/transit/tribe and cp
# 5) have to be able to join created fields to queried field
# 6)

#
class SummaryBuilder:

    def __init__(self, report_type):
        self.REPORT_TYPES = ['transit_data', 'revenue', 'expense', 'fund_balance']
        self.report_type = report_type

    def get_current_report_year(self):
        current_year = get_current_summary_report_year()
        years = [current_year-2, current_year-1, current_year]
        return years


    def get_model(self):
        '''returns the appropriate model for the given report type'''
        if self.report_type == "revenue":
            return revenue
        elif self.report_type == "transit_data":
            return transit_data
        elif self.report_type == "expense":
            return expense
        elif self.report_type == "fund_balance":
            return fund_balance
        else:
            raise Http404("Report type does not exist. -4")

    def get_model_data(self):
        '''returns the appropriate model for the given report type'''
        if self.report_type == "revenue":
            return revenue.objects.filter(revenue_source__inactive_flag=False)
        elif self.report_type == "transit_data":
            return transit_data.objects
        elif self.report_type == "expense":
            return expense.objects
        elif self.report_type == "fund_balance":
            return fund_balance.objects
        else:
            raise Http404("Report type does not exist. -4")

    def get_metric_model(self):
        '''returns the appropriate metric model for the given report type'''
        if self.report_type == "revenue":
            return revenue_source
        elif self.report_type == "transit_data":
            return transit_metrics
        elif self.report_type == "expense":
            return expense_source
        elif self.report_type == "fund_balance":
            return fund_balance_type
        else:
            raise Http404("Report type does not exist. -5")

    def get_metric_model_data(self):
        '''returns the appropriate metric model for the given report type'''
        if self.report_type == "revenue":
            return revenue_source.objects.filter(inactive_flag=False)
        elif self.report_type == "transit_data":
            return transit_metrics.objects
        elif self.report_type == "expense":
            return expense_source.objects
        elif self.report_type == "fund_balance":
            return fund_balance_type.objects
        else:
            raise Http404("Report type does not exist. -5")

    def get_metric_model_name(self):
        '''Returns the metric model as a string.'''
        if self.report_type == "revenue":
            return 'revenue_source'
        elif self.report_type == "transit_data":
            return 'transit_metric'
        elif self.report_type == "expense":
            return 'expense_source'
        elif self.report_type == "fund_balance":
            return 'fund_balance_type'
        else:
            raise Http404("Report type does not exist. -6")

    def get_metric_id_field_name(self):
        '''Returns the name of the field name of the id field in the metric model as a string.'''
        if self.report_type == "transit_data":
            return 'transit_metric_id'
        else:
            metric_model = self.get_metric_model()
            return metric_model.__name__ + '_id'



class ReportAgencyDataTableBuilder(SummaryBuilder):
    def __init__(self, report_type, target_organization):
        super().__init__(report_type)
        self.REPORT_TYPES = ['transit_data', 'revenue', 'expense', 'fund_balance']
        self.years = self.get_current_report_year()
        self.report_type = report_type
        self.target_organization = target_organization
        self.services_offered = self.get_all_services_offered()
        self.summary_report = SummaryReport()
        self.data = self.get_model_data_for_agency()
        self.heading_list = []
        self.agency_classification = self.get_agency_classification()
        self.metrics = self.get_metrics_for_agency_classification()
        self.current_report_year = max(self.years)
        self.last_report_year = self.current_report_year-1
        self.revenue_type_list = [('Local', 'Operating'), ('State', 'Operating'), ('Federal', 'Operating'), ('Other', 'Operating'),('Federal', 'Capital'), ('State', 'Capital'), ('Local', 'Capital')]
        self.vanpooling_revenue = self.get_vanpool_revenue()
        self.farebox_revenue = self.get_farebox_revenue()
        self.filtered_metrics = self.filter_out_unused_metrics()
        self.filtered_heading_list = self.create_headings()


    def get_metrics_for_agency_classification(self):
        if self.report_type in ['transit_data', 'revenue']:
            return self.get_metric_model().objects.filter(agency_classification = self.agency_classification).order_by('order_in_summary')
        else:
            return self.get_metric_model().objects.all()


    def get_model_data_for_agency(self):
        return self.get_model_data().filter(organization_id = self.target_organization, year__in = self.years)
        #filtered by get_metrics_for_agency_classification() and filters(may need to build dictionary or move the query dict up a class higher)

    def get_metric_model_fields(self):
        return self.get_metric_model_data().all()

    def get_agency_classification(self):
        return organization.objects.get(id = self.target_organization).summary_organization_classifications_id


    def create_headings(self):
        if self.report_type == 'revenue':
            filtered_revenue_type = self.get_metric_model().objects.filter(id__in = self.filtered_metrics).values_list('government_type', 'funding_type').distinct()
            filtered_heading_list = [x for x in self.revenue_type_list if x in filtered_revenue_type]
            return filtered_heading_list
        elif self.report_type == 'expense':
            filtered_heading_list = list(self.get_metric_model().objects.filter(id__in = self.filtered_metrics).values_list('heading').distinct())
            filtered_heading_list = [heading[0] for heading in filtered_heading_list]
            return filtered_heading_list
        elif self.report_type == 'fund_balance':
            filtered_heading_list = ['Ending Balances, December 31']
            return filtered_heading_list



    def filter_out_unused_metrics(self):
            metric_to_eliminate = []
            for metric in list(self.metrics):
                print(metric)
                check_list = []
                if self.report_type == 'revenue':
                    filtered_data = self.data.filter(revenue_source__name = metric, year__in = self.years)
                elif self.report_type == 'expense':
                    filtered_data = self.data.filter(expense_source__name=metric, year__in=self.years)
                elif self.report_type == 'fund_balance':
                    filtered_data = self.data.filter(fund_balance_type__name = metric, year__in = self.years)
                else:
                    filtered_metrics = None
                    return filtered_metrics
                [check_list.append(datum.reported_value) for datum in filtered_data]
                print(check_list)
                if list(set(check_list)) == [None]:
                    metric_to_eliminate.append(metric.id)
                    if self.report_type == 'fund_balance':
                        metric_to_eliminate = [metric for metric in metric_to_eliminate if metric is not 15]
            filtered_metrics = self.metrics.exclude(id__in = metric_to_eliminate)
            return filtered_metrics


    def revenue_totals_and_exceptions(self, metric):
        if metric == 'Farebox Revenues':
            data_row = self.farebox_revenue
            return data_row
        elif metric == 'Vanpooling Revenue':
            data_row = self.vanpooling_revenue
            return data_row
        elif metric == 'Other Operating Subtotal':
            return self.data.filter(revenue_source__government_type = 'Other', revenue_source__funding_type = 'Operating').values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
        elif metric == 'Total (Excludes Capital Revenue)':
            return self.data.filter(revenue_source__funding_type='Operating').values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
        elif metric == 'Total State Capital':
            return self.data.filter(revenue_source__government_type='State',revenue_source__funding_type='Capital').values('year').annotate(reported_value=Sum('reported_value')).order_by('year')
        elif metric == 'Total Federal Capital':
            return self.data.filter(organization_id=self.target_organization, year__in=self.years,revenue_source__government_type='Federal',revenue_source__funding_type='Capital').values('year').annotate(reported_value=Sum('reported_value')).order_by('year')
        elif metric == 'Total Local Capital':
            return self.data.filter(organization_id = self.target_organization, year__in = self.years, expense_source_id__in = [1,6]).values('year').annotate(reported_value=Sum('reported_value')).order_by('year')
        elif metric == 'Total Debt Service':
            return self.data.filter(organization_id=self.target_organization, year__in=self.years,expense_source_id__in=[4,5]).values('year').annotate(reported_value=Sum('reported_value')).order_by('year')
        elif metric == 'Total':
            return self.data.filter(organization_id = self.target_organization, year__in = self.years).values('year').annotate(reported_value=Sum('reported_value')).order_by('year')

    def get_vanpool_revenue(self):
        return transit_data.objects.filter(organization_id =self.target_organization, year__in=self.years,transit_metric__name='Farebox Revenues',
                                           transit_mode_id =3).values('reported_value').order_by('year')

    def get_farebox_revenue(self):
        return transit_data.objects.filter(organization_id=self.target_organization, year__in=self.years,transit_metric__name='Farebox Revenues', transit_mode_id__in=[1,2,4,5,6,7,8,9,10,11], reported_value__isnull=False).values('year').annotate(reported_value = Sum('reported_value')).order_by('year')

    def get_all_services_offered(self):
        '''gets the data needed to build header navigation for filters'''
        if self.report_type in ['transit_data', ]:
            services_offered = service_offered.objects.filter(organization_id =self.target_organization, service_mode_discontinued=False).order_by('transit_mode_id')
            return services_offered
        elif self.report_type in ['expense', 'fund_balance', 'revenue']:
            pass
        else:
            raise Http404

    def filter_metrics_by_service(self):
        filtered_transit_metric_dictionary = {}
        for service in self.services_offered:
            metric_to_eliminate = []
            for metric in self.metrics:
                check_list = []
                filtered_data = self.data.filter(administration_of_mode = service.administration_of_mode, transit_mode_id = service.transit_mode_id, transit_metric__name = metric)
                [check_list.append(datum.reported_value) for datum in filtered_data]
                if list(set(check_list)) == [None]:
                    metric_to_eliminate.append(metric.id)
            filtered_metrics = self.metrics.exclude(id__in=metric_to_eliminate)
            filtered_transit_metric_dictionary[service] = filtered_metrics
        return filtered_transit_metric_dictionary



    def add_labels_to_data(self, data):
        count = 1
        data_list = []
        data = list(data)
        for datum in data:
            if datum['reported_value'] == None:
                datum['reported_value'] = 0
            data_list.append(('year{}'.format(count), datum['reported_value']))
            count +=1
        return data_list


    def create_total_funds_by_source(self):
        total_funds_by_source = SummaryTable()
        self.create_revenues()
        self.create_investments()

    def create_revenues(self):
        heading = [('source', 'Revenues'),('year1', ''), ('year2', ''), ('year3', ''), ('percent_change', ''), ('role', 'heading')]
        heading_dic = dict(heading)
        self.total_funds_by_source.add_row_component(heading_dic)
        revenue_types = [['Local', 'Other'], ['State'], ['Federal'], ['Total Revenues (all sources)']]
        for revenue_type in revenue_types:
            if revenue_type[0] =='Total Revenues (all sources)':
                revenue_row = revenue.objects.filter(organization_id=self.target_organization, year__in=self.years, revenue_source__funding_type='Operating', reported_value__isnull=False).values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
            else:
                revenue_row = revenue.objects.filter(organization_id=self.target_organization, year__in=self.years, revenue_source__government_type__in=revenue_type, revenue_source__funding_type='Operating', reported_value__isnull=False).values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
            if not revenue_row:
                continue
            data_list = self.add_labels_to_data(revenue_row)
            percent_change = self.generate_percent_change(data_list)
            if revenue_type[0] == 'Total Revenues (all sources)':
                heading = revenue_type
                data_list = [('source', heading)] + data_list + [('percent_change', percent_change), ('role', 'subtotal')]
            else:
                heading = "{} Revenues".format(revenue_type[0])
                data_list = [('source', heading)] + data_list + [('percent_change', percent_change), ('role', 'body')]
            data_dic = dict(data_list)
            self.total_funds_by_source.add_row_component(data_dic)


    def create_investments(self):
        total_investment_list = []
        heading = [('source', 'Investments'), ('year1', ''), ('year2', ''), ('year3', ''), ('percent_change', ''), ('role', 'heading')]
        heading_dic = dict(heading)
        self.totals.add_row_component(heading_dic)
        revenue_types = [('Operating Investment'), ('Local Capital Investment'), ('State', 'Capital'), ('Federal', 'Capital'), ('Other Investment'), ('Total Investment')]
        for revenue_type in revenue_types:
            if revenue_type[0] == ['Operating Investment']:
                investment_row = transit_data.objects.filter(organization_id=self.target_organization, year__in = self.years, transit_metric_id = 9, reported_value__isnull= False).values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
                heading = revenue_type[0]
            if not investment_row:
                continue
            investment_list = self.add_labels_to_data(investment_row)
            if revenue_type[0] != 'Total Investment':
                total_investment_list.append([row[1] for row in investment_list])
            percent_change = self.generate_percent_change(investment_list)


    #TODO break this into two functions
    def get_table_types_by_organization(self):
        if self.report_type == 'transit_data':
            operating_report = SummaryTable()
            service_dictionary = self.filter_metrics_by_service()
            for service in service_dictionary.keys():
                heading = [('transit_metric', '{} ({})'.format(service.transit_mode.name, service.administration_of_mode)), ('year1', ''), ('year2', ''), ('year3', ''), ('percent_change', ''), ('role', 'heading')]
                heading = dict(heading)
                operating_report.add_row_component(heading)
                for metric in service_dictionary[service]:
                    data_row = self.data.filter(administration_of_mode = service.administration_of_mode, transit_mode_id = service.transit_mode_id, transit_metric__name = metric).values('reported_value').order_by('year')
                    if not data_row:
                        continue
                    data_list = self.add_labels_to_data(data_row)
                    percent_change = self.generate_percent_change(data_list)
                    data_list = [('transit_metric', str(metric))] + data_list + [('percent_change',percent_change), ('role', 'body')]
                    data_dic = dict(data_list)
                    operating_report.add_row_component(data_dic)
            return operating_report
        elif self.report_type in ['revenue', 'expense', 'fund_balance']:
            summary_report = SummaryTable()
            if self.filtered_heading_list == None:
                return None
            op_count = 1
            for heading in self.filtered_heading_list:
                if self.report_type == 'revenue':
                    metric_list = self.filtered_metrics.filter(government_type=heading[0], funding_type=heading[1]).values_list('name', flat = True)
                elif self.report_type == 'expense':
                    metric_list = self.filtered_metrics.filter(heading = heading).values_list('name', flat = True)
                elif self.report_type == 'fund_balance':
                    metric_list = self.filtered_metrics.values_list('name', flat=True)
                metric_list = list(metric_list)
                if heading == 'Local Capital Expenditures':
                    metric_list = metric_list + ['Total Local Capital']
                if heading == 'Debt Service':
                    metric_list = metric_list + ['Total Debt Service']
                if len(metric_list) == 0:
                    continue
                blank_heading_list = [('year1', ''), ('year2', ''), ('year3', ''), ('percent_change', ''), ('role', 'heading')]
                if heading[1] == 'Operating':
                    heading_row = [('source', 'Operating Related Revenues')]
                    heading_row = heading_row + blank_heading_list
                    heading_row = dict(heading_row)
                    if op_count < 2:
                        summary_report.add_row_component(heading_row)
                    op_count +=1
                else:
                    if heading == ('Federal', 'Capital'):
                        heading_row = [('source', 'Federal capital grant revenues')]
                    elif heading == ('State', 'Capital'):
                        heading_row = [('source', 'State capital grant revenue')]
                    else:
                        heading_row = [('source', heading)]
                    heading_row = heading_row + blank_heading_list
                    heading_row = dict(heading_row)
                    summary_report.add_row_component(heading_row)
                for metric in metric_list:
                    if metric in ['Farebox Revenues', 'Vanpooling Revenue', 'Other Operating Subtotal', 'Total (Excludes Capital Revenue)', 'Total Federal Capital', 'Total State Capital', 'Total Local Capital', 'Total Debt Service', 'Total']:
                        data_row = self.revenue_totals_and_exceptions(metric)
                    else:
                        if self.report_type == 'revenue':
                            data_row = self.data.filter(revenue_source__name=metric).values('reported_value').order_by('year')
                        elif self.report_type == 'expense':
                            data_row = self.data.filter(expense_source__name = metric).values('reported_value').order_by('year')
                        elif self.report_type == 'fund_balance':
                            data_row = self.data.filter(fund_balance_type__name = metric).values('reported_value').order_by('year')
                    if not data_row:
                        continue
                    data_list = self.add_labels_to_data(data_row)
                    percent_change = self.generate_percent_change(data_list)
                    if metric in ['Other Operating Subtotal', 'Total (Excludes Capital Revenue)', 'Total Federal Capital', 'Total State Capital', 'Total Local Capital', 'Total Debt Service', 'Total']:
                        data_list = [('source', metric)] + data_list + [('percent_change',percent_change), ('role', 'subtotal')]
                    elif metric in ['Other-Advertising', 'Other-Interest', 'Other-Gain (Loss) on Sale of Assets', 'Other-MISC']:
                        data_list = [('source', metric)] + data_list + [('percent_change', percent_change),('role', 'other_indent')]
                    else:
                        data_list = [('source', metric)] + data_list + [('percent_change', percent_change), ('role', 'body')]
                    data_dic = dict(data_list)
                    summary_report.add_row_component(data_dic)
            return summary_report



class SummaryReport:
    def __init__(self):
        self.summary_tables = {}

    def add_table(self, summary_table):
        self.summary_tables.update(summary_table)


class SummaryTable:

    def __init__(self):
        self.table_components = []

    def add_row_component(self, table_component):
        self.table_components.append(table_component)


class SummaryTableComponent:

    def __init__(self,  data):
        self.data = data




class SummaryDataReportBuilder(ReportAgencyDataTableBuilder):

    def __init__(self):
        self.summary_report = SummaryReport()
        self.data = self.get_model_data_for_agency()


    def get_table_types_by_organization(self):
        if self.target_organization[0].summary_organization_classifications == "Transit":
            operating_report = SummaryTable()
            for service in self.services_offered:
                op_data = self.data.filter(administration_of_mode = service.administration_of_mode, transit_mode_id = service.transit_mode_id).order_by('transit_metrics.order_in_summary')
                # gonna need to add a heading in here
                operating_report.add_table_component(op_data)

            SummaryReport.add_table(operating_report)



        else:
            pass
#
#
# #    def build




