import itertools

from django.db import transaction
from django.db.models import Sum
from django.forms import modelformset_factory
from django.http import Http404
from django.shortcuts import redirect

from Panacea.models import service_offered, revenue, transit_data, expense, fund_balance, revenue_source, \
    transit_metrics, expense_source, fund_balance_type, transit_mode, summary_organization_progress, organization
from Panacea.utilities import get_current_summary_report_year, get_all_data_steps_completed
from django import forms
from django.forms import modelformset_factory, BaseModelFormSet, ModelForm


class SummaryBuilder:

    def __init__(self, report_type):
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


class SummaryDataEntryBuilder(SummaryBuilder):
    '''This class constructs all of the forms needed to collect summary data'''

    def __init__(self, report_type, target_organization, form_filter_1=None, form_filter_2=None):
        super().__init__(report_type)
        self.REPORT_TYPES = ['transit_data', 'revenue', 'expense', 'fund_balance']

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


        print(self.current_increment)

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
        if self.report_type == "revenue":
            self.max_form_increment = 7
        elif self.report_type == "transit_data":
            self.max_form_increment = service_offered.objects.filter(organization=self.target_organization).count()
        elif self.report_type == "expense":
            self.max_form_increment = 1
        elif self.report_type == "fund_balance":
            self.max_form_increment = 1
        else:
            raise Http404("Report type does not exist. -2")

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
            print(transit_mode.objects.get(name=self.form_filter_1))
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
        print(all_metric_ids_and_years)
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

        form_metrics = model.filter(organization=self.target_organization)
        return form_metrics

    def get_widgets(self):
        '''Used to build widgets dynamically based on form type.'''

        if self.report_type == 'transit_data':
            widget_attrs = {'class': 'form-control validate-field'}
        else:
            widget_attrs = {'class': 'form-control grand-total-sum validate-field', 'onchange': 'findTotal_wrapper();'}

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

    def get_formsets_labels_and_masking_class(self):
        '''Builds formsets by year with labels and masking classes'''
        my_formset_factory = self.create_model_formset_factory()
        form_querysets = self.get_form_queryset()

        formsets = {}
        i = 0
        for year_x in ['this_year', 'previous_year', 'two_years_ago']:
            formsets[year_x] = my_formset_factory(
                queryset=form_querysets.filter(year=self.year - i).order_by(self.get_metric_id_field_name()),
                prefix=year_x)
            i += 1
        formset_labels = form_querysets.filter(year=self.year).order_by(self.get_metric_id_field_name()).values_list(
            self.get_metric_model_name() + "__name", flat=True)
        if self.report_type != "transit_data":
            masking_class = ['Money'] * len(formset_labels)
        else:
            masking_class = form_querysets.filter(year=self.year).order_by(self.get_metric_id_field_name()).values_list(
                self.get_metric_model_name() + "__form_masking_class", flat=True)

        return formsets, formset_labels, masking_class

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

            revenue_list_order_type = ['Operating', 'Capital']
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

    def go_to_next_form(self):
        self.current_increment = self.current_increment + 1
        if self.current_increment > self.max_form_increment:
            org_progress = summary_organization_progress.objects.get(organization=self.target_organization)
            if self.report_type == 'fund_balance':
                org_progress.ending_balances = True
                org_progress.save()
                if get_all_data_steps_completed(self.target_organization.id):
                    return redirect('submit_data')
                else:
                    raise Http404("You are not ready to submit your data.  Please be sure you have reviewed each section.")
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

                new_report_type = self.REPORT_TYPES[self.REPORT_TYPES.index(self.report_type)+1]
                return redirect('summary_reporting_type', new_report_type)
        else:
            self.form_filter_1 = self.nav_filters[self.current_increment - 1][0]
            self.form_filter_2 = self.nav_filters[self.current_increment - 1][1]
            return redirect('summary_reporting_filters', self.report_type, self.form_filter_1, self.form_filter_2)


class SummaryDataEntryTemplateData:
    '''Simple class that uses the SummaryDataEntryBuilder to create data needed in the template'''

    def __init__(self, data_entry_factory, report_type):
        self.formsets, self.formset_labels, self.masking_class = data_entry_factory.get_formsets_labels_and_masking_class()
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


class ConfigurationBuilder(SummaryBuilder):

    def __init__(self, report_type):
        super().__init__(report_type)
        self.REPORT_TYPES = ['organization', 'transit_data', 'revenue', 'expense', 'fund_balance']
        self.primary_field_name, self.other_fields_list = self.get_model_fields()

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

        if self.get_data_relationship_one_2_one():
            widgets = {'id': forms.NumberInput(),
                       'name': forms.TextInput(attrs={'class': 'form-control AJAX_instant_submit',
                                                      'data-form-name': "summary_configures"}),
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


