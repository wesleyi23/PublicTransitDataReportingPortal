from Panacea.utilities import *
from Panacea.models import *
from itertools import chain
import collections

#init object that reads all the stuff
#super class reads the data dictionary and defines parameters
#super class holds all the methods
# each report is potentially a class object that inhertis methods from aggregate report
# each report has a name property that gets accessed whenever a new object is created, but the methods have all the same name
#has all the paramters of data dictionary, has a generate method that gets run when the class gets initialized
#init object looks at report list, generates the requisite objects, downloads them all as data objects
#TODO camelCase for methods, _for objects,
import csv

class AggregateReport:
    def __init__(self, size, report):
        self.report = report
        self.current_report_year = get_current_summary_report_year()
        self.reportAttributeDictionary = reportAttributeDictionary
        self.years = reportAttributeDictionary[report]['years']
        self.size = size
        self.models = reportAttributeDictionary[report]['models']
        self.report_years = self.generateReportYear()
        self.classification =reportAttributeDictionary[report]['classification']
        self.aggregation = reportAttributeDictionary[report]['aggregation']
        self.metrics = reportAttributeDictionary[report]['metrics']
        self.agency_list = self.evaluateReportSize()


    def evaluateReportSize(self):
        # separates out very large and smaller transits
     return reportAttributeDictionary[self.size]


    def toExcel(self, final_list):
        '''excel function that writes everything out'''
        if self.size != 'all transits':
            with open("{}__{}.csv".format(self.report, self.size), 'w', newline="") as f:
                writer = csv.writer(f)
                for k in final_list:
                    writer.writerow(k)
        else:
            with open(r"C:\Users\SchumeN\Documents\{}.csv".format(self.report), 'w', newline="") as f:
                writer = csv.writer(f)
                for k in final_list:
                    writer.writerow(k)



    def findOtherOperatingSubtotal(self):
        other_subtotal = revenue.objects.filter(organization_id__in=self.agency_list, organization__summary_organization_classifications=self.classification, year__in = self.report_years,
                               revenue_source__government_type="Other", revenue_source__funding_type='Operating').values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
        for i in other_subtotal:
            i['revenue_source__name'] = 'Other Operating Subtotal'
        return other_subtotal


    def addOtherOperatingSubtotalToQuery(self, result):
        '''this function creates an other operating subtotal for the revenue section'''
        other_subtotal = self.findOtherOperatingSubtotal()
        for index, value in enumerate(result):  #iterates through indexes and values
            if value.get('revenue_source__name') == 'Other-Advertising':
                result = list(chain(result[:index-1], other_subtotal, result[index:])) #adds the other operating subtotal to the list at the precise point
                break
        return result

    def getLandBank(self):
        landbank = revenue.objects.filter(revenue_source_id = 96, year__in = self.report_years).values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
        for i in landbank:
            i['revenue_source__name'] = "Land Bank Agreement & Credits"
        return landbank

    def addLandBank(self, result):
        '''adds a landbank column to the State Capital section, so that it doesn't get included in totals'''
        landbank = self.getLandBank()
        result = list(chain(landbank, result))
        return result



    def findFareboxRevenueAndVanpool(self):
        farebox = transit_data.objects.filter(organization_id__in=self.agency_list,
                                              organization__summary_organization_classifications=self.classification,
                                              year__in=self.report_years, transit_metric_id=10,
                                              transit_mode_id__in=[1, 2, 4, 5, 6, 7, 8, 9, 10]).values('year','transit_metric__name').annotate(reported_value=Sum('reported_value'))
        vanpool = transit_data.objects.filter(organization_id__in=self.agency_list, organization__summary_organization_classifications=self.classification,
                                              year__in=self.report_years, transit_metric_id=10, transit_mode_id__in=[3]).values('year', 'transit_metric__name').annotate(reported_value=Sum('reported_value'))
        for i in vanpool:
            i['transit_metric__name'] = 'Vanpooling Revenue'
        return farebox, vanpool

    def addFareboxRevenueToAList(self, result):
        farebox, vanpool = self.findFareboxRevenueAndVanpool()
        result = list(chain(farebox, vanpool, result))
        return result

    def addFareboxAndVanpoolToTotals(self, result):
        farebox, vanpool = self.findFareboxRevenueAndVanpool()
        zipped = zip(farebox, vanpool, result)
        for fb, vp, total in zipped:
            total['reported_value'] = fb['reported_value'] + vp['reported_value'] + total['reported_value']
        return result

    def generatePercentChange(self, data_list):
        '''function for adding percent change to summary tables'''
        try:
            percent_change = round(((data_list[-1] - data_list[-2]) / data_list[-2]) * 100,2)
        except ZeroDivisionError:
            if data_list[-1] == data_list[-2] == 0:
                percent_change = '-'
            else:
                percent_change = 100.00
        data_list.append(percent_change)
        return data_list


    def generateReportYear(self):
        # mechanism for generating the report_years variable, necessary as years covered are 1, 3, and six
        # dynamically generates the years based on the range variable, returns a list
        if self.years == 1:
            return [self.current_report_year] #current report year turned into a list here
        else:
            report_years = []
            for year in range(0, self.years):
                report_years.append(self.current_report_year - year)
            return report_years #list returned here

    def pull_farebox_revenue(self):
        result = transit_data.objects.filter(organization_id__in=self.agency_list, organization__summary_organization_classifications=6)

        #TODO turn most things into strings, write them out with appropriate markers (dollars, commas, etc.)
        #TODO filter the queryset based on list, and then do that in order
        #TODO assess what's unique to this set of problems/more generalizable, rearrange code on that basis
        #TODO good documentation



    #TODO this is kind of a mess, and may only work for aggregate reporting, which is fine!
    def callData(self):
        data_tables = {}
        # if clause exists to apply the > 1 million/< 1 million metric to the code, as its one of the new nuances to this issue
        if self.classification == 6:
            for key, metric in self.metrics.items():
                aggregation = self.aggregationSelector(metric[0])
                if metric[0] == transit_data:
                    for mode in list(metric[1].values()): #could probably do this less weirdly, need to make this more dynamic and build it off a function related ot services offered
                        result = self.getModel(metric).filter(organization_id__in = self.agency_list, organization__summary_organization_classifications=self.classification, year__in = self.report_years,
                                               transit_mode__rollup_mode__in=mode).values("year", *aggregation).annotate(reported_value = Sum('reported_value')).order_by('transit_metric__order_in_summary')
                else:
                    result = self.getModel(metric).filter(organization_id__in=self.agency_list, organization__summary_organization_classifications=self.classification,year__in=self.report_years,
                                                          **metric[1]).values("year", *aggregation).annotate(reported_value=Sum('reported_value')).order_by('{}__order_in_summary'.format(aggregation[0].replace('__name', '')))

                if self.report == "Financial Summary" and metric[0] != transit_data:
                    result2 = self.getModel(metric).filter(organization_id__in = self.agency_list, organization__summary_organization_classifications=self.classification, year__in = self.report_years, **metric[1]).values('year').annotate(reported_value = Sum('reported_value')).order_by('year')
                    if key == 'Operating Related Revenues':
                        result = self.addFareboxRevenueToAList(result)
                        result = self.addOtherOperatingSubtotalToQuery(result)
                        result2 = self.addFareboxAndVanpoolToTotals(result2)
                    elif key == 'State Capital Grant Revenues':
                        result = self.addLandBank(result)
                    result = list(chain(result, result2))
                data_tables[key] = result

        else:
            for key, metric in self.metrics.items():
                result = self.getModel(metric).filter(organization__summary_organization_classifications=self.classification, year__in = self.report_years,
                                               **metric[1], ).values()
                data_tables[key] = result
        return data_tables

        #gotta revise this so it functions on a list of lists basis, reads things, digests headings, and filters by mode

    def filterEmptyDataLists(self, data_list):
        '''logic for finding and catching empty data in  function form'''
        if list(set(data_list[1:])) == [None]:  # this gets rid of empty datasets
            data_list = []
            return data_list
        elif list(set(data_list[1:])) == [0.0]:
            data_list = []
            return data_list
        else:
            if data_list[0] != 'Employees - FTEs':
                data_list[1:] = [0 if v is None else v for v in data_list[1:]]  # list comprehension replaces nulls with 0s for processing
                data_list[1:] = [int(i) for i in data_list[1:]]
                if list(set(data_list[1:])) == [0]:
                    data_list = []
                    return data_list
                else:
                    return data_list
            else:
                data_list[1:] = [0.0 if v is None else v for v in data_list[1:]]  # list comprehension replaces nulls with 0s for processing
                data_list[1:] = [round(i, 1) for i in data_list[1:]]
                if list(set(data_list[1:])) == [0.0]:
                    data_list = []
                    return  data_list
                else:
                    return data_list

    def cleanData(self, data_tables):
        final_list = []
        mode_heading = ""
        transit_mode_list = []
        if len(self.report_years) > 1:
            for key, value in data_tables.items():
                chartLength = len(self.report_years)+1
                blank_heading = [""]*chartLength
                heading = [key] + blank_heading
                final_list.append(heading)
                data_list = []
                for v in value:
                    if "transit_mode__rollup_mode" in v.keys():
                        mode_key = v['transit_mode__rollup_mode'] + " Services"
                        mode_heading = [mode_key] + blank_heading
                        if mode_heading not in transit_mode_list:
                            transit_mode_list.append(mode_heading)
                            final_list.append(mode_heading)
                    named_key = [i for i in v.keys() if i.endswith('name')]
                    if named_key == []:
                        if key == "Operating Related Revenues":
                            metric = 'Total (Excludes Capital Revenue)'
                        elif key == 'Other expenditures':
                            continue
                        elif key == 'Ending balances, December 31':
                            metric = 'Total'
                        elif key == 'Debt service':
                            metric = 'Total Debt service'
                        else:
                            key = key.replace(' Revenues', '')
                            key = key.replace(' expenditures', '')
                            metric = 'Total ' + key
                    else:
                        named_key = named_key[0]
                        metric = v[str(named_key)]

                    if len(data_list) == 0:
                        data_list.append(metric)
                        data_list.append(v["reported_value"])
                    else:
                        data_list.append(v["reported_value"])
                    if len(data_list) == len(self.report_years)+1:
                        data_list  =self.filterEmptyDataLists(data_list)
                        if data_list == []:
                            continue
                        data_list = self.generatePercentChange(data_list)
                        final_list.append(data_list)
                        data_list = []
        return final_list

#TODO get farebox revenues in there
#TODO write out to excel


    def getModel(self, metric):
        #calls the metric and puts it into the query
       return metric[0].objects


    def aggregationSelector(self, metric):
        if self.aggregation == "metrics":
            if metric == transit_data and self.report == "Financial Summary": #needed to build in something very specific for financial summary
                return ["transit_mode__rollup_mode", "transit_metric__name"]
            if metric == transit_data:
                return ["transit_metric__name"]
            if metric == revenue:
                return ["revenue_source__name"]
            if metric == expense:
                return ["expense_source__name"]
            if metric == fund_balance:
                return ["fund_balance_type__name"]







class FinancialSummary(AggregateReport):
    def __init__(self, size):
        self.report = "Financial Summary"
        super().__init__(size, self.report)



#1. figure out how to filter and transform data (procedurally?)
#2. need to combine datasets into lists, maybe to a dic-list, and include % change,
#3 order based on summary data
#4 add in some other data in Financial Summary class
#5  output to excel


def run_reports(report_list, size):
    fs = FinancialSummary(size)
    results = fs.callData()
    results = fs.cleanData(results)
    fs.toExcel(results)




reportAttributeDictionary = { 'separate tables for agencies with populations under a million': [3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,
                                                                                                22,23,24,25,26,27,28,29,30,31,32,34,35], 'all transits' :[3,4,5,6,7,8,9,10,11,12,13,14, 15,16,17,18,19,20,21,
                                                                                                22,23,24,25,26,27,28,29,30,31,32,33,34,35],
                              'Financial Summary': {'years':3, 'aggregation':'metrics', 'mode_aggregation':[transit_data, {'transit_mode_id__rollup_mode__in':['Fixed Route', 'Commuter Rail', 'Light Rail', 'Route Deviated', 'Demand Response', 'Vanpool']}], 'models':[transit_data, revenue, expense, fund_balance], 'classification':6, 'metrics':{ "Annual Operating Information":[transit_data,  {'transit_mode__rollup_mode__in':['Fixed Route', 'Commuter Rail', 'Light Rail', 'Route Deviated', 'Demand Response', 'Vanpool']}], 'Operating Related Revenues':[revenue, {"revenue_source__funding_type": 'Operating'}], 'Federal Capital Grant Revenues':[revenue, {"revenue_source__government_type": 'Federal',"revenue_source__funding_type": 'Capital'}], 'State Capital Grant Revenues':[revenue, {"revenue_source__government_type": 'State', "revenue_source__funding_type": "Capital"}], 'Local capital expenditures': [expense, {"expense_source_id__in": [1]}], 'Other expenditures': [expense,{"expense_source_id__in": [2,3]}], 'Debt service':[expense,{"expense_source_id__in": [4,5]}],
                                                                                                        'Ending balances, December 31':[fund_balance, {"fund_balance_type_id__in": [6,7,8,9,10,11,12,13,14]}]}},
                              'Statewide Financial Revenues': {'years':1, 'aggregation':'agencies', 'models': [revenue,expense, transit_data], 'classification':6, 'metrics':{'Sales or local tax':[revenue, (revenue_source, [12,14,21])], 'Fare Revenue (all modes except vanpool)':[transit_data, (transit_metrics, 10), (transit_mode, [1,2,4,5,6,7,8,9,10])], 'Vanpool revenue': [transit_data, (transit_metrics, [10]), (transit_mode, [3])], 'Federal operating revenue':[revenue, (revenue_source.government_type, 'Federal'), (revenue_source.funding_type, 'Operating')], 'State operating revenue':[revenue, (revenue_source.government_type, 'State'), (revenue_source.funding_type,'Operating')], 'Other operating revenue':[revenue, (revenue_source.government_type, 'Other'), (revenue_source.funding_type, 'Operating')],
                                                                                                                                                                              'State capital revenue':[revenue, 'State', 'Capital'], 'Federal capital revenue':[revenue, 'Federal', 'Capital'] }},
                              'Statewide Financial Expense': {'years':1, 'aggregation':'agencies', 'models': [revenue, expense, transit_data], 'classification':6, 'metrics':{'Fixed Route':[transit_data, (transit_metrics, [9]), (transit_mode.rollup_mode, ["Fixed Route"])], 'Route Deviated': [transit_data, (transit_metrics, [9]), (transit_mode.rollup_mode, ["Route Deviated"])], "Demand Response":[transit_data,(transit_metrics, [9]), (transit_mode.rollup_mode, ["Demand Response"])], "Vanpool":[transit_data,(transit_metrics, [9]), (transit_mode.rollup_mode, ["Vanpool"])], "All Rail Modes":[transit_data,(transit_metrics, [9]), (transit_mode.rollup_mode, ["Light Rail", "Commuter Rail"])], "Debt Service":[expense, (expense_source, [4,5])],
                                                                                                                                                                              'Other':[expense,(expense_source, [2])], 'Capital Expense':[[expense, (expense_source, [1])], [revenue, (revenue_source.funding_type, "Capital")], ("operation_type","sum")], 'Depreciation':[expense, (expense_source, [3])]}},
                              'Statewide Investments': {'years':5, 'models': [revenue, transit_data], 'classification':6, 'metrics':{"Local Capital Investment":[expense,(expense_source, 1)], "State Capital Investment":[revenue, (revenue_source.government_type, "State"), (revenue_source.funding_type, "Capital")], "Federal Capital Investment":[revenue, (revenue_source.government_type, "Federal"), (revenue_source.funding_type, "Capital")], "Other Capital Investment": [expense, (expense_source, [2,4,5])]} },
                              'Statewide Revenues': {'years':5, 'models': [transit_data,revenue], 'classification':6, 'metrics':{"Local Revenues":[[transit_data, (transit_metrics, [10])], [revenue, (revenue_source.government_type, ["Local", "Other"])], [expense, (expense_source, [1])], ("operation_type", "sum")], 'State Revenues':[revenue, (revenue_source.government_type, "State")], 'Federal Revenues':[revenue, (revenue_source.government_type, 'Federal')]}},
                               'Service Mode Tables': {'years':1, 'aggregation':'modes', 'mode_aggregation':[service_offered, transit_mode.rollup_mode], 'models':[transit_data], 'classification':6, 'metrics': {'System Category':[organization, organization.classification], 'Revenue Vehicle Hours by Service Mode': [transit_data, (transit_metrics, 1)], 'Revenue Vehicle Miles by Service Mode': [transit_data, (transit_metrics,2)], 'Passenger Trips by Service Mode': [transit_data, (transit_metrics, 5)], 'Farebox Revenues by Service Mode': [transit_data, (transit_metrics, 10)],
                                           'Operating Expenses by Service Mode': [transit_data, (transit_metrics,9)], 'Operating Cost per Passenger Trip': [transit_data, (transit_metrics, 9),(transit_metrics, 5), ('operation_type', 'division')], 'Operating Cost per Revenue Vehicle Hour': [transit_data, (transit_metrics, 9), (transit_metrics, 1), ('operation_type', 'division')],
                                           'Passenger Trips per Revenue Vehicle Hour': [transit_data, (transit_metrics, 5),(transit_metrics, 1), ('operation_type', 'division')], 'Passenger Trips per Revenue Vehicle Miles': [transit_data, (transit_metrics, 5),(transit_metrics, 2), ('operation_type', 'division')], 'Revenue Vehicle Hours per Employee': [transit_data, (transit_metrics, 1),(transit_metrics, 8), ('operation_type', 'division')],
                                           'Farebox Recovery Ratio': [transit_data, (transit_metrics,10), (transit_metrics, 9), ('operation_type', 'division')]}},
                                'Operation Stats': {'years':1, 'aggregation':('modes', 'agencies'), 'mode_aggregation':[service_offered, transit_mode.rollup_mode], 'models': [transit_data], 'classification':6, 'metrics': {'System Category':[organization, organization.classification], 'Revenue Vehicle Hours by Service Mode': [transit_data, (transit_metrics, 1)], 'Revenue Vehicle Miles by Service Mode': [transit_data, (transit_metrics,2)], 'Passenger Trips by Service Mode': [transit_data, (transit_metrics, 5)], 'Farebox Revenues by Service Mode': [transit_data, (transit_metrics, 10)],
                                           'Operating Expenses by Service Mode': [transit_data, (transit_metrics,9)], 'Operating Cost per Passenger Trip': [transit_data, (transit_metrics, 9),(transit_metrics, 5), ('operation_type', 'division')], 'Operating Cost per Revenue Vehicle Hour': [transit_data, (transit_metrics, 9), (transit_metrics, 1), ('operation_type', 'division')],
                                           'Passenger Trips per Revenue Vehicle Hour': [transit_data, (transit_metrics, 5),(transit_metrics, 1), ('operation_type', 'division')], 'Passenger Trips per Revenue Vehicle Miles': [transit_data, (transit_metrics, 5),(transit_metrics, 2), ('operation_type', 'division')], 'Revenue Vehicle Hours per Employee': [transit_data, (transit_metrics, 1),(transit_metrics, 8), ('operation_type', 'division')],
                                           'Farebox Recovery Ratio': [transit_data, (transit_metrics,10), (transit_metrics, 9), ('operation_type', 'division')]}},
                                'Statewide Ferries': {'years':3, 'aggregation':'metrics', 'models': [transit_data, revenue], 'classification': 2},
                                'Statewide Community Providers': {'years':3, 'aggregation':'metrics', 'models':[transit_data, revenue], 'classification':1}


}