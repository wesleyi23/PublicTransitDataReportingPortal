from django_pandas.io import read_frame
import pandas as pd
from .models import depreciation, revenue_source, revenue, fund_balance, expense, transit_data, organization
import numpy as np
from django.db.models import Sum, Q



def create_statewide_expense_table(year):
    from .models import depreciation
    df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year=year, transit_metric_id=9).values('organization__name',
    'transit_mode__rollup_mode').annotate(reported_value=Sum('reported_value')))

    depreciation = read_frame(depreciation.objects.filter(year = year).values('organization__name').annotate(reported_value = Sum('reported_value')))
    debt_service = read_frame(fund_balance.objects.filter(organization__summary_organization_classifications_id = 6, year = year, fund_balance_type = 12).values('organization__name').annotate(reported_value = Sum('reported_value')))
    expenses = read_frame(expense.objects.filter(organization__summary_organization_classifications_id =6, year = year, expense_source_id__in = [1,2]).values('expense_source__name', 'organization__name').annotate(reported_value = Sum('reported_value')))
    revenue_capital = read_frame(revenue.objects.filter(organization__summary_organization_classifications_id = 6, year = year, revenue_source__funding_type = 'Capital').values('organization__name').annotate(reported_value = Sum('reported_value')))
    depreciation['data_type'] = 'Depreciation'
    debt_service['data_type'] = 'Debt Service'
    print(depreciation)
    print(debt_service)
    print(expenses)
    print(revenue_capital)










def create_statewide_revenue_table(year):
    revenues = read_frame(revenue.objects.filter(organization__summary_organization_classifications_id=6, year=year,reported_value__isnull=False).values('organization__name',
    'revenue_source_id__government_type','revenue_source_id__funding_type').annotate(reported_value=Sum('reported_value')).exclude(revenue_source_id__in = [63,64]))
    fares = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year = year, reported_value__isnull = False, transit_metric_id = 10, transit_mode_id__in = [1,2,4,5,6,7,8,9,10,11]).values('organization__name').annotate(fare_revenue = Sum('reported_value'))).set_index('organization__name')
    vanpool = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year = year, reported_value__isnull = False, transit_metric_id = 10, transit_mode_id__in = [3]).values('organization__name').annotate(vanpool_revenue = Sum('reported_value'))).set_index('organization__name')

    revenues['title'] = revenues['revenue_source_id__government_type'] + ' ' + revenues['revenue_source_id__funding_type'] + ' Revenue'
    df = revenues.pivot(index = 'organization__name', columns= 'title', values = 'reported_value')
    df = pd.concat([df, fares, vanpool], axis = 1).fillna(0)
    df = df.reset_index()
    subtotal = pd.DataFrame(df[df['index'] != 'Sound Transit'].sum(axis = 0)).transpose()
    subtotal.at[0, 'index'] = 'Sub-Totals'
    total = pd.DataFrame(df.sum(axis = 0)).transpose()
    total.at[0, 'index'] = 'Statewide Revenue Total'
    df = pd.concat([df[df['index'] != 'Sound Transit'], subtotal, df[df['index'] == 'Sound Transit'], total], axis = 0).set_index('index')
    df['Total Revenue'] = df.sum(axis=1)
    df = df.reset_index()
    df = df.rename(columns = {'Local Operating Revenue':'Sales or Local Tax', 'fare_revenue': 'Fare Revenue (all modes except vanpool', 'vanpool_revenue':'Vanpool Revenue', 'index':'Revenues'})
    df = df.reindex(columns = ['Revenues', 'Sales or Local Tax', 'Fare Revenue (all modes except vanpool', 'Vanpool Revenue','Federal Operating Revenue', 'State Operating Revenue', 'Other Operating Revenue','Federal Capital Revenue',
                               'State Capital Revenue', 'Total Revenue'])
    return df


def create_dependent_statistics(df):
    '''associated with generate mode by agency table function'''
    df['Passenger Trips/Revenue Hour'] = df['Passenger Trips']/df['Revenue Vehicle Hours']
    df['Passenger Trips/Revenue Mile'] = df['Passenger Trips']/ df['Revenue Vehicle Hours']
    df['Revenue Hours/FTE'] = df['Revenue Vehicle Hours']/df['Employees - FTEs']
    df['Operating Expenses/Revenue Hour'] = df['Operating Expenses']/df['Revenue Vehicle Hours']
    df['Operating Expenses/ Revenue Mile'] = df['Operating Expenses']/df['Revenue Vehicle Miles']
    df['Operating Expenses/Passenger Trip'] = df['Operating Expenses']/df['Passenger Trips']
    df['Farebox Recovery Ratio'] = df['Farebox Revenues']/df['Operating Expenses']*100
    df = df.replace(np.inf, 0)
    return df

def organization_names_and_classifications(df):
    '''code to add classifications and organization names to the mode by agency table'''
    org_names = df.organization__name.tolist()
    list_of_orgs = organization.objects.filter(name__in=org_names).values('name', 'classification')
    classification_dic = dict(zip([name['name'] for name in list_of_orgs], [name['classification'] for name in list_of_orgs]))
    df['classification'] = df['organization__name'].apply(lambda x: classification_dic[x])
    return df

def sum_and_average_function(category, df):
    '''builds the sum and average rows for each mode'''
    if "Statewide" in category:  # builds statewide version; excludes other aggregate sums and averages
        statewidedf = df[df.classification.isin(['Urban', 'Small Urban', 'Rural'])]
        sums = statewidedf[['Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles', 'Total Vehicle Miles','Passenger Trips', 'Employees - FTEs', 'Operating Expenses', 'Farebox Revenues']].sum()
        avgs = statewidedf[['Passenger Trips/Revenue Hour', 'Passenger Trips/Revenue Mile', 'Revenue Hours/FTE','Operating Expenses/Revenue Hour', 'Operating Expenses/ Revenue Mile','Operating Expenses/Passenger Trip', 'Farebox Recovery Ratio']].mean()
    else:
        sums = df[df.classification == category][['Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles', 'Total Vehicle Miles','Passenger Trips', 'Employees - FTEs', 'Operating Expenses', 'Farebox Revenues']].sum()
        avgs = df[df.classification == category][['Passenger Trips/Revenue Hour', 'Passenger Trips/Revenue Mile', 'Revenue Hours/FTE','Operating Expenses/Revenue Hour', 'Operating Expenses/ Revenue Mile', 'Operating Expenses/Passenger Trip','Farebox Recovery Ratio']].mean()
    changeddf = pd.DataFrame(pd.concat([sums, avgs])).transpose()
    changeddf['classification'] = 'Totals/Averages'
    changeddf['organization__name'] = category
    changeddf = changeddf.set_index('organization__name')
    df = pd.concat([df, changeddf])
    return df


def generate_mode_by_agency_tables(mode, year):
    '''this function generates stats for each transit mode by agency'''
    #TODO condense this, functionalize; figure out what to do about Central Transit
    if mode == 'Demand Response':
        # DR Taxi services is its own mode that gets collapsed in, so have to build some special bits of this
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year=year,
                                                    reported_value__isnull=False, transit_mode__name__in=['Demand Response', 'Demand Response Taxi Services'],
                                                    transit_metric_id__in=[1, 2, 3, 4, 5, 8, 9, 10]).values('organization__name', 'transit_metric__name').annotate(reported_value=Sum('reported_value')))
    else:
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year=year,reported_value__isnull=False, transit_mode__name= mode, transit_metric_id__in=[1, 2, 3, 4, 5, 8, 9, 10]).values('organization__name','transit_metric__name').annotate(reported_value = Sum('reported_value')))
    df = df.pivot(index = 'organization__name', columns = 'transit_metric__name', values = 'reported_value').fillna(0)
    df = df.reset_index()
    df = organization_names_and_classifications(df)
    df = create_dependent_statistics(df)
    df = df.set_index('organization__name')
    if ['Rural'] in df.classification.unique():  # check to see if there's more than one type of agency in the list
        categories = ['Urban', 'Small Urban', 'Rural', 'Statewide {}'.format(mode)]
        for category in categories:
            df = sum_and_average_function(category, df)
    else: # code for the more rarely used modes, where there's only a couple of agencies in a mode, i.e. Commuter Rail, Light Rail
        category = 'Statewide {}'.format(mode)
        df = sum_and_average_function(category, df)
    df = df.reindex(columns = ['classification', 'Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles', 'Total Vehicle Miles', 'Passenger Trips','Employees - FTEs',
                               'Operating Expenses', 'Farebox Revenues','Passenger Trips/Revenue Hour', 'Passenger Trips/Revenue Mile', 'Revenue Hours/FTE', 'Operating Expenses/Revenue Hour',
                               'Operating Expenses/ Revenue Mile', 'Operating Expenses/Passenger Trip', 'Farebox Recovery Ratio'])
    df = df.reset_index()
    heading_list =  df.columns.tolist()
    heading_list = [mode, 'System Category'] + heading_list[2:]
    col_list = df.columns.tolist()
    col_list = [i.replace(' ', '') for i in col_list]
    col_list = [i.replace('/', '') for i in col_list]
    col_list = [i.replace('-FTEs', '') for i in col_list]
    df.columns = col_list
    return df, heading_list


def generate_performance_measure_table(metric, years):
    if len(metric) == 2:
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years,reported_value__isnull=False).values('year', 'rollup_mode__name').annotate(
        reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric[0]))/ Sum('reported_value', filter = Q(transit_metric__name = metric[1]))))
    else:
        df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years, reported_value__isnull=False).values('year', 'rollup_mode__name').annotate(reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric))))
    df = df.dropna(thresh=3)
    df = df.pivot(index = 'rollup_mode__name', columns = 'year', values= 'reported_value')
    rollup_mode_list = ['Fixed Route', 'Route Deviated', 'Demand Response', 'Vanpool', 'Commuter Rail', 'Light Rail']
    df = df.reindex(rollup_mode_list)
    if metric in ["Revenue Vehicle Hours", 'Revenue Vehicle Miles', 'Passenger Trips', 'Farebox Revenues', 'Operating Expenses']:
        df = df.append(df.sum().rename('Total'))
    if metric == ('Farebox Revenues', 'Operating Expenses'):
        df = df*100
    df = df.reset_index()
    df['percent_change'] = ((df.iloc[:, 6] - df.iloc[:, 5]) / df.iloc[:, 5]) * 100
    df = df.fillna('-')
    df = df.replace(np.inf, 100.00)
    df.columns = ['title', 'year1', 'year2', 'year3', 'year4', 'year5', 'year6', 'percent_change']
    return df
