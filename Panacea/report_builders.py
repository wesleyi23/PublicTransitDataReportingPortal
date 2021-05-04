from Panacea.utilities import *
from Panacea.models import *
from itertools import chain
from collections import OrderedDict

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
    def __init__(self, report, size):
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



    #builing report specification methods

    def evaluateReportSize(self):
    # separates out very large and smaller transits
        return reportAttributeDictionary[self.size]

    def generateReportYear(self):
        # mechanism for generating the report_years variable, necessary as years covered are 1, 3, and six
        # dynamically generates the years based on the range variable, returns a list
        if self.years == 1:
            return [self.current_report_year]  # current report year turned into a list here
        else:
            report_years = []
            for year in range(0, self.years):
                report_years.append(self.current_report_year - year)
            return report_years  # list returned here

    def getModel(self, metric):
        # calls the metric and puts it into the query
        return metric[0].objects

    def aggregationSelector(self, metric):
        '''organizes aggregation process, governs how these things are rolled up into queries by changing what is in the values part of the annotate function'''
        if self.aggregation == "metrics":
            if metric == transit_data and self.report == "Financial Summary":  # needed to build in something very specific for financial summary
                return ["transit_mode__rollup_mode", "transit_metric__name"]
            if metric == transit_data:
                return ["transit_metric__name"]
            if metric == revenue:
                return ["revenue_source__name"]
            if metric == expense:
                return ["expense_source__name"]
            if metric == fund_balance:
                return ["fund_balance_type__name"]
        elif self.aggregation == 'agencies':  #this looks at the aggregation level agencies
            return["organization_id__name"]



    #Querying data methods

    def getAllAgencyNamesFromClassification(self):
        names = organization.objects.filter(summary_organization_classifications=self.classification).values_list('name', flat = True).order_by('name')
        return names
    def findOtherOperatingSubtotal(self):
        '''makes the other operating subtotal for the Financial Summary'''
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
        '''this function looks for the landbank so that it doesn't get added to everything else'''
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
        '''this function reads and builds the vanpool and farebox revenue rows for the revenue'''
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
        '''this adds farebox revenue to the results list of revenues'''
        farebox, vanpool = self.findFareboxRevenueAndVanpool()
        result = list(chain(farebox, vanpool, result))
        return result

    def addFareboxAndVanpoolToTotals(self, result):
        '''this adds farebox and vanpool to the total values'''
        farebox, vanpool = self.findFareboxRevenueAndVanpool()
        zipped = zip(farebox, vanpool, result)
        for fb, vp, total in zipped:
            total['reported_value'] = fb['reported_value'] + vp['reported_value'] + total['reported_value']
        return result




    #data cleaning methods

    def orderADictionary(self, dictionary):
        new_dic = {}
        if self.report == "Statewide Financial Expenses":
            report_order = ['Fixed Route', 'Route Deviated', 'Demand Response', 'Vanpool', 'All Rail Modes', 'Debt Service', 'Other', 'Capital Expenses']
        for category in report_order:
            new_dic[category] = dictionary.get(category)
        return new_dic

    def combineData(self, name_of_category, list_of_names, input_keys, output_key, dictionary):
        iterating_list = []
        combined_list = []
        for key in input_keys:
            iterating_list+= dictionary[key]
        for name in list_of_names:
            total = 0
            for value in iterating_list:
                if value[name_of_category] == name:
                    if value['reported_value'] == None:
                        total+=0
                    else:
                        total+= value['reported_value']
            combined_list.append({name_of_category:name, 'reported_value':total})
        dictionary[output_key] = combined_list
        for key in input_keys:
            del dictionary[key]
        return dictionary


    def exitSound(self):
        agency_list_without_Sound = [i for i in self.agency_list if i != 33]
        return agency_list_without_Sound

    def rearrangeSound(self, result, metric):
        soundList = [i for i in result if i['organization_id__name'] == 'Sound Transit']  # filter out Sound to its own list
        noSoundList = [i for i in result if i['organization_id__name'] != 'Sound Transit']  # make a list without Sound
        newSubtotal = self.querySubtotal(metric)
        newTotal = self.queryTotal(metric)
        result = list(chain(noSoundList, newSubtotal, soundList, newTotal))
        return result
        # insert between subtotal and total

    def querySubtotal(self, metric):
        newSubtotal = self.getModel(metric).filter(organization_id__in=self.exitSound(),
                                                   organization__summary_organization_classifications=self.classification,
                                                   year__in=self.report_years, **metric[1]).values("year").annotate(
            reported_value=Sum('reported_value'))
        newSubtotal = newSubtotal[0]
        newSubtotal['organization_id__name'] = 'Subtotal'
        newSubtotal = [(newSubtotal)]
        return newSubtotal

    def queryTotal(self, metric):
        newTotal = self.getModel(metric).filter(organization_id__in=self.agency_list,
                                                organization__summary_organization_classifications=self.classification,
                                                year__in=self.report_years, **metric[1]).values("year").annotate(
            reported_value=Sum('reported_value'))
        if self.report == 'Statewide Financial Revenues':
            newTotal = newTotal[0]
            newTotal['organization_id__name'] = 'Statewide revenue total'
            newTotal = [newTotal]
        elif self.report == "Statewide Financial Expenses":
            newTotal = newTotal[0]
            newTotal['organization_id__name'] = 'Statewide obligations total'
            newTotal = [newTotal]
        return newTotal

    def generatePercentChange(self, data_list):
        '''function for adding percent change to summary tables'''
        try:
            percent_change = round(((data_list[-1] - data_list[-2]) / data_list[-2]) * 100, 2)
        except ZeroDivisionError:
            if data_list[-1] == data_list[-2] == 0:
                percent_change = '-'
            else:
                percent_change = 100.00
        data_list.append(percent_change)
        return data_list

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
                data_list[1:] = [0 if v is None else v for v in
                                 data_list[1:]]  # list comprehension replaces nulls with 0s for processing
                data_list[1:] = [int(i) for i in data_list[1:]]
                if list(set(data_list[1:])) == [0]:
                    data_list = []
                    return data_list
                else:
                    return data_list
            else:
                data_list[1:] = [0.0 if v is None else v for v in
                                 data_list[1:]]  # list comprehension replaces nulls with 0s for processing
                data_list[1:] = [round(i, 1) for i in data_list[1:]]
                if list(set(data_list[1:])) == [0.0]:
                    data_list = []
                    return data_list
                else:
                    return data_list

    def formattingStrings(self, data_list):
        if self.report in ["Statewide Financial Revenues", "Statewide Financial Expenses"]:
            data_list[1:] = list(map(lambda x: "${:,}".format(int(x)), data_list[1:]))
        else:
            if data_list[0] not in ['Revenue Vehicle Hours', 'Total Vehicle Hours', 'Passenger Trips',
                                'Total Vehicle Miles', 'Revenue Vehicle Miles',
                                'Diesel Fuel Consumed (gallons)', 'Gasoline Fuel Consumed (gallons)',
                                'Propane Fuel Consumed (gallons)', 'Electricity Consumed (kWh)',
                                'CNG Fuel Consumed (therms)']:
                data_list[1:4] = list(map(lambda x: "${:,}".format(x), data_list[1:4]))
            elif data_list[0] == 'Employees - FTEs':
                data_list[1:4] = list(map(lambda x: "{:,.1f}".format(x), data_list[1:4]))
            else:
                data_list[1:4] = list(map(lambda x: "{:,}".format(x), data_list[1:4]))
            data_list[4] = "{:,.2f}".format(data_list[4])
        return data_list

       #core functional methods

    def toExcel(self, final_list):
        #TODO add a file path form, because you can select an out path from here
        '''excel function that writes everything out'''
        if self.size != 'all transits': #this if clause outputs a slightly different version of the excel file name based on selection mechanis
            with open("{}__{}.csv".format(self.report, self.size), 'w', newline="") as f:
                writer = csv.writer(f)
                for k in final_list:
                    writer.writerow(k)
        else:
            with open(r"C:\Users\SchumeN\Documents\{}.csv".format(self.report), 'w', newline="") as f:
                writer = csv.writer(f)
                for k in final_list:
                    writer.writerow(k)

    def callData(self):
        data_tables = {}
        # if clause exists to apply the > 1 million/< 1 million metric to the code, as its one of the new nuances to this issue
        if self.classification == 6:
            for key, metric in self.metrics.items():
                aggregation = self.aggregationSelector(metric[0])
                if metric[0] == transit_data and aggregation[0] != "organization_id__name": # made this to route some tranist data to the second part of the if clause
                    ls = list(metric[1].values())[0]
                    result = ''
                    for mode in ls:  # could probably do this less weirdly, need to make this more dynamic and build it off a function related ot services offered
                        mode_result = self.getModel(metric).filter(organization_id__in=self.agency_list,
                                                                   organization__summary_organization_classifications=self.classification,
                                                                   year__in=self.report_years,
                                                                   transit_mode__rollup_mode__in=[mode]).values("year",
                                                                                                                *aggregation).annotate(
                            reported_value=Sum('reported_value')).order_by('transit_metric__order_in_summary')
                        if result == '':
                            result = mode_result
                        else:
                            result = list(chain(result, mode_result))
                else:
                    result = self.getModel(metric).filter(organization_id__in=self.agency_list,
                                                          organization__summary_organization_classifications=self.classification,
                                                          year__in=self.report_years,
                                                          **metric[1]).values("year", *aggregation).annotate(
                        reported_value=Sum('reported_value')).order_by('{}__order_in_summary'.format(aggregation[0].replace('__name', '')))
                    if aggregation[0] == "organization_id__name": # made this so that one could get results without the order by, and that order by organization name, as opposed to metrics
                        result = self.getModel(metric).filter(organization_id__in=self.agency_list,
                                                              organization__summary_organization_classifications=self.classification,
                                                              year__in=self.report_years,
                                                              **metric[1]).values("year", *aggregation).annotate(reported_value=Sum('reported_value')).order_by("organization_id__name")
                        result = self.rearrangeSound(result, metric)
                        #generate subtotal
                        #generate total
                if self.report == "Financial Summary" and metric[0] != transit_data:
                    result2 = self.getModel(metric).filter(organization_id__in=self.agency_list,
                                                           organization__summary_organization_classifications=self.classification,
                                                           year__in=self.report_years, **metric[1]).values(
                        'year').annotate(reported_value=Sum('reported_value')).order_by('year')
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
                result = self.getModel(metric).filter(
                    organization__summary_organization_classifications=self.classification, year__in=self.report_years,
                    **metric[1], ).values()
                data_tables[key] = result
        return data_tables

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
                        data_list = self.formattingStrings(data_list)
                        final_list.append(data_list)
                        data_list = []
        return final_list


class OneYearReport(AggregateReport):

    def modify_agency_names(self, names):
        """method to order the names of agencies so that they matcch the table"""
        names = [i for i in names if i != "Sound Transit"]
        if self.report == "Statewide Financial Revenues":
            names = names +['Subtotal', 'Sound Transit', 'Statewide revenue total']
        elif self.report == "Statewide Financial Expenses":
            names = names + ['Subtotal', 'Sound Transit', 'Statewide obligations total']
        return names


    def addDepreciation(self, agency):
        '''pulls depreciation numbers and adds them at the very end'''
        if agency == 'Subtotal':
            total = expense.objects.filter(expense_source_id = 3, year__in = self.report_years, organization__summary_organization_classifications= self.classification, organization_id__in= self.exitSound()).values('year').annotate(reported_value = Sum('reported_value'))
        elif agency == 'Statewide obligations total':
            total = expense.objects.filter(expense_source_id=3, year__in=self.report_years,
                                           organization__summary_organization_classifications=self.classification).values('year').annotate(reported_value=Sum('reported_value'))
        else:
            total = expense.objects.filter(expense_source_id=3, year__in=self.report_years, organization__name =agency).values('year').annotate(reported_value=Sum('reported_value'))
        if total[0]['reported_value'] == None:
            return 0
        else:
            return total[0]['reported_value']




    def cleanData(self, data_tables):
        '''overridden cleanData method for expenses and revenues that filters through the data table'''
        final_list = []
        organization_names = self.getAllAgencyNamesFromClassification()
        organization_names = self.modify_agency_names(organization_names)
        if self.report == "Statewide Financial Expenses":
            data_tables = self.combineData('organization_id__name', organization_names, ['Local Capital Expense', 'All Capital'], "Capital Expenses", data_tables)
            data_tables = self.orderADictionary(data_tables)
        column_heads = list(data_tables.keys())
        if self.report == "Statewide Financial Revenues":
            column_heads = ['Agency Name'] + column_heads + ['Total Revenue'] # builds a column heading list
        elif self.report == "Statewide Financial Expenses": #TODO functionalize this one
            column_heads = ['Expenses'] + column_heads + ['Total Annual Expenses'] + ['Depreciation']
        final_list.append(column_heads)
        for agency in organization_names: #for loop by agency name
            agency_list = [agency]
            for key, value in data_tables.items():
                found = False # this is used to id if a particular value was never input (eg, the mode doesnt exist for the agency)
                for v in value:
                    if v['organization_id__name'] == agency:
                        agency_list.append(v['reported_value']) #adds just the reported value to the agency list
                        found = True
                if found == False:
                    agency_list.append(0)  #adds a 0 if the particular value was never input
            agency_list = [0 if i is None else i for i in agency_list] # subs out the Nones
            agency_list.append(sum(agency_list[1:]))  # makes the total revenues column
            if self.report == 'Statewide Financial Expenses':
                depreciation = self.addDepreciation(agency)
                agency_list.append(depreciation)
            agency_list = self.formattingStrings(agency_list) # formats the strings with dollar signs and commas
            final_list.append(agency_list)
        return final_list  # returns the list

class FiveYearReport(AggregateReport):
    '''methods and overrides for Statewide Investments and Revenues'''
    def callData(self):
        data_tables = {}
        # if clause exists to apply the > 1 million/< 1 million metric to the code, as its one of the new nuances to this issue
        if self.classification == 6:
            for key, metric in self.metrics.items():
                result = self.getModel(metric).filter(organization_id__in=self.agency_list,
                                              organization__summary_organization_classifications=self.classification,
                                              year__in=self.report_years,**metric[1]).values("year").annotate(reported_value=Sum('reported_value'))
                data_tables[key] = result
        return data_tables

    def percentOfTotal(self, final_list, total):
        for ls in final_list[1:]:
            percent_of_total = round((ls[-1]/total)*100, 2)
            ls.append(percent_of_total)
        return final_list


    def cleanData(self, data_tables):
        final_list = []
        if self.report != "Financial Summary":
            heading_list = [self.report] + [self.report_years] + ['Percent of Total']
        else:
            heading_list = ['Total Funds By Source'] + [self.report_years] + ['One Year Change (%)']
        final_list.append(heading_list)
        if self.report == 'Statewide Revenues':
            data_tables = self.combineData('year', self.report_years, ['Fare Revenues', 'Local Tax', 'Local Capital'], 'Local Revenues', data_tables)
        row_list = []
        for key, value in data_tables.items():
            for v in value:
                if len(row_list) == 0:
                    row_list.append(key)
                    row_list.append(v['reported_value'])
                else:
                    row_list.append(v['reported_value'])
            if self.report == "Financial Summary":
                row_list = self.generatePercentChange(row_list)
            final_list.append(row_list)
        final_list_sums = [sum(i) for i in final_list[1:]]
        final_list_sums = ['Total'] + final_list_sums
        if self.report == "Financial Summary":
            final_list_sums = self.generatePercentChange(final_list_sums)
            final_list.append(final_list_sums)
        else:
            final_list.append(final_list_sums)
            total = final_list_sums[-1]
            final_list = self.percentOfTotal(final_list, total)
        return final_list

class RandomText(AggregateReport):
    def __init__(self, size):
        self.report_year = get_current_summary_report_year()
        self.report_years = [self.report_year, self.report_year-1]
        self.random_text_dictionary = random_text_dictionary
        self.agency_list = self.evaluateReportSize()
        pass

    def cleanDataAndMakeList(self, data):
        '''takes data and puts it in a list'''
        return 0

    def callData(self):
        for key, value in random_text_dictionary.items():
            #need to add an if clause in here to check if there is more than one model, if so, iterates through list, chains them together
            filtered_values = self.getModel(value['model']).objects.filter(*value['metric'],year__in = self.report_years, organization__summary_organization_classifications = value['classification']).values('year').annotate(reported_value = Sum('reported_value'))
            list_of_data = self.cleanDataAndMakeList(filtered_values)
# when need to aggregate multiple calls, data type is list here
        return list_of_data

    def cleanData(self, list_of_data):
            pass

#need a method to calculate what percentage of local tax is sound transit
# need a method to caluclate farebox % of operating
# need a method for all revenues
# need a method for all capital

#for specificied value types, going to build a dictionary so they can be used in secondary random text, secondary random text uses tuples as keys, and thus
#contains instructions to check this results dictionary to make relevant percentages





def run_reports(report_list, size):
    for report in report_list:
        if report in ["Statewide Financial Revenues", "Statewide Financial Expenses"]:
            agg = OneYearReport(report, size)
            results = agg.callData()
            results = agg.cleanData(results)
            agg.toExcel(results)
        elif report in ['Statewide Investments', 'Statewide Revenues']:
            agg = FiveYearReport(report, size)
            results = agg.callData()
            print(results)
            results = agg.cleanData(results)
            agg.toExcel(results)
        else:
            agg = AggregateReport(report, size)
            results = agg.callData()
            results = agg.cleanData(results)
            agg.toExcel(results)





reportAttributeDictionary = { 'separate tables for agencies with populations under a million': [3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,
                                                                                                22,23,24,25,26,27,28,29,30,31,32,34,35], 'all transits' :[3,4,5,6,7,8,9,10,11,12,13,14, 15,16,17,18,19,20,21,
                                                                                                22,23,24,25,26,27,28,29,30,31,32,33,34,35],
                              'Financial Summary': {'years':3, 'aggregation':'metrics', 'mode_aggregation':[transit_data, {'transit_mode_id__rollup_mode__in':['Fixed Route', 'Commuter Rail', 'Light Rail', 'Route Deviated', 'Demand Response', 'Vanpool']}], 'models':[transit_data, revenue, expense, fund_balance], 'classification':6, 'metrics':{ "Annual Operating Information":[transit_data,  {'transit_mode__rollup_mode__in':['Fixed Route', 'Commuter Rail', 'Light Rail', 'Route Deviated', 'Demand Response', 'Vanpool']}], 'Operating Related Revenues':[revenue, {"revenue_source__funding_type": 'Operating'}], 'Federal Capital Grant Revenues':[revenue, {"revenue_source__government_type": 'Federal',"revenue_source__funding_type": 'Capital'}], 'State Capital Grant Revenues':[revenue, {"revenue_source__government_type": 'State', "revenue_source__funding_type": "Capital"}], 'Local capital expenditures': [expense, {"expense_source_id__in": [1]}], 'Other expenditures': [expense,{"expense_source_id__in": [2,3]}], 'Debt service':[expense,{"expense_source_id__in": [4,5]}],
                                                                                                        'Ending balances, December 31':[fund_balance, {"fund_balance_type_id__in": [6,7,8,9,10,11,12,13,14]}]}},
                              'Statewide Financial Revenues': {'years':1, 'aggregation':'agencies', 'models': [revenue,expense, transit_data], 'classification':6, 'metrics':{'Sales or local tax':[revenue, {"revenue_source_id__in": [12,14,21]}], 'Fare Revenue (all modes except vanpool)':[transit_data, {"transit_metric_id__in": [10], "transit_mode_id__in":[1,2,4,5,6,7,8,9,10]}], 'Vanpool revenue': [transit_data, {"transit_metric_id__in": [10], "transit_mode_id__in": [3]}], 'Federal operating revenue':[revenue, {"revenue_source__government_type": 'Federal', "revenue_source__funding_type":'Operating'}], 'State operating revenue':[revenue, {"revenue_source__government_type": 'State', "revenue_source__funding_type":'Operating'}], 'Other operating revenue':[revenue, {"revenue_source__government_type": 'Other', "revenue_source__funding_type": 'Operating'}],
                                                                                                                                                                              'State capital revenue':[revenue, {"revenue_source__government_type":'State', "revenue_source__funding_type":'Capital'}], 'Federal capital revenue':[revenue, {"revenue_source__government_type":'State', "revenue_source__funding_type":'Capital'}]}},
                              'Statewide Financial Expenses': {'years':1, 'aggregation':'agencies', 'models': [revenue, expense, transit_data], 'classification':6, 'metrics':{'Fixed Route':[transit_data, {"transit_metric_id__in": [9], "transit_mode__rollup_mode": "Fixed Route"}], 'Route Deviated': [transit_data, {"transit_metric_id__in": [9], "transit_mode__rollup_mode": "Route Deviated"}], "Demand Response":[transit_data,{"transit_metric_id__in": [9], "transit_mode__rollup_mode": "Demand Response"}], "Vanpool":[transit_data,{"transit_metric_id__in": [9], "transit_mode__rollup_mode": "Vanpool"}], "All Rail Modes":[transit_data,{"transit_metric_id__in": [9], "transit_mode__rollup_mode__in": ["Light Rail", "Commuter Rail"]}], "Debt Service":[expense, {"expense_source_id__in": [4,5]}],
                                                                                                                                                                              'Other':[expense,{"expense_source_id__in": [2]}], 'Local Capital Expense':[expense, {"expense_source_id__in": [1]}], "All Capital": [revenue, {"revenue_source__funding_type": "Capital"}]}},
                              'Statewide Investments': {'years':5, 'aggregation':'all', 'models': [revenue, transit_data], 'classification':6, 'metrics':{"Operating Investment":[transit_data, {'transit_metric_id__in': [10]}], "Local Capital Investment":[expense,{"expense_source_id": 1}], "State Capital Investment":[revenue, {"revenue_source__government_type": "State", "revenue_source__funding_type": "Capital"}], "Federal Capital Investment":[revenue, {"revenue_source__government_type": "Federal","revenue_source__funding_type": "Capital"}], "Other Capital Investment": [expense, {"expense_source_id__in": [2,4,5]}]}},
                              'Statewide Revenues': {'years':5, 'aggregation':'all', 'models': [transit_data,revenue], 'classification':6, 'metrics':{"Fares":[transit_data, {"transit_metric_id__in": [10]}],'Local Tax':[revenue, {"revenue_source__government_type__in": ["Local", "Other"]}], "Local Capital":[expense, {"expense_source_id__in": [1]}], 'State Revenues':[revenue, {"revenue_source__government_type": "State"}], 'Federal Revenues':[revenue, {"revenue_source__government_type": 'Federal'}]}},
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


random_text_dictionary = {'Revenue Vehicle Hours':{'model':[transit_data], 'classification': 6, 'metric':{'transit_metric_id__in':'[1]'}},
'Revenue Vehicle Miles':{'model':[transit_data], 'classification':6, 'metric':{'transit_metric_id__in':'[3]'}}, 'Passenger Trips':{'model':[transit_data], 'classification':6,'metric':{'transit_metric_id__in':'[5]'}},
          'Farebox Revenues':{'model':[transit_data], 'classification':6,'metric':{'transit_metric_id__in':'[10]'}}, 'Operating Expenses':{'model':[transit_data], 'classification':6,'metric':{'transit_metric_id__in':'[9]'}},
    ('Fixed Route Services', 'Revenue Vehicle Hours'):{'model':[transit_data], 'classification': 6, 'metric':{'transit_metric_id__in':'[1]', 'transit_mode__rollup_mode':'Fixed'}},
('Fixed Route Services', 'Passenger Trips'):{'model':[transit_data], 'classification': 6, 'metric':{'transit_metric_id__in':'[5]', 'transit_mode__rollup_mode':'Fixed'}},
'Local revenues':[{"Fares":{'model':[transit_data], 'classification':6, 'metric':{"transit_metric_id__in": [10]}},'Local Tax':{'model':[revenue], 'classification':6, 'metric':{"revenue_source__government_type__in": ["Local", "Other"]}}, "Local Capital":{'model':[expense], 'classification':6, 'metric':{"expense_source_id__in": [1]}}}],
                          'State revenues':{'model':[revenue], 'classification':6, 'metric':{"revenue_source__government_type": "State"}}, 'Federal revenues':{'model':[revenue],
'classification':6, 'metric':{"revenue_source__government_type": 'Federal'}}, 'Local tax revenues':{'model': [revenue], 'classification':6, 'metric':{'revenue_source__government_type':'Local'}},
                          'Local capital investment':{'model':[expense], 'classification':6, 'metric':{"expense_source_id__in": [1]}}, 'State capital investment':{'model':[revenue], 'classification':6, 'metric':{'revenue_source__government_type':'State', 'revenue_source__funding_type':'Capital'}},
                          'Federal capital investment':{'model':[revenue], 'classification':6, 'metric':{'revenue_source__government_type':'Federal', 'revenue_source__funding_type':'Capital'}},
                          'Other capital investment':{'model':[expense], 'classification':6, 'metric':{"expense_source_id__in": [2,4,5]}}


}

