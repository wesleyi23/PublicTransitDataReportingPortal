from django_pandas.io import read_frame
import pandas as pd
from .models import depreciation, revenue_source, revenue, fund_balance, expense, transit_data, organization
import numpy as np
from django.db.models import Sum, Q

def create_statewide_expense_table(year):
     df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications_id=6, year=year, transit_metric_id=9).values('organization__name',
     'transit_mode__rollup_mode').annotate(reported_value=Sum('reported_value')))
     debt_service = read_frame(fund_balance.objects.filter(organization__summary_organization_classifications_id = 6, year = year, fund_balance_type = 12).values('organization__name').annotate(reported_value = Sum('reported_value')))
     expenses = read_frame(expense.objects.filter(organization__summary_organization_classifications_id =6, year = year, expense_source_id__in = [1,2,3]).values('expense_source__name', 'organization__name').annotate(reported_value = Sum('reported_value')))
     revenue_capital = read_frame(revenue.objects.filter(organization__summary_organization_classifications_id = 6, year = year, revenue_source__funding_type = 'Capital').values('organization__name').annotate(reported_value = Sum('reported_value')))
     debt_service['data_type'] = 'Debt Service'
     expenses = expenses.rename(columns = {'expense_source__name': 'data_type'})
     revenue_capital['data_type'] = 'Non-local Capital'
     df = df.rename(columns = {'transit_mode__rollup_mode':'data_type'})
     expenses = expenses.pivot(index= 'organization__name', columns = 'data_type', values='reported_value')
     debt_service = debt_service.pivot(index='organization__name', columns='data_type', values='reported_value')
     revenue_capital = revenue_capital.pivot(index='organization__name', columns='data_type', values='reported_value')
     df = df.pivot(index='organization__name', columns='data_type', values='reported_value')
     merged = pd.concat([df, expenses, debt_service, revenue_capital], axis=1)
     merged = merged.fillna(0)
     merged['All Rail Modes'] = merged['Commuter Rail'] + merged['Light Rail']
     merged['Capital Expenses'] = merged['Local Capital Funds'] + merged['Non-local Capital']
     merged = merged.drop(['Ferry', 'Monorail', 'Commuter Rail', 'Light Rail', 'Local Capital Funds', 'Non-local Capital'], axis = 1)
     merged = merged.reset_index()
     subtotal = pd.DataFrame(merged[merged['organization__name'] != 'Sound Transit'].sum(axis = 0)).transpose()
     subtotal.at[0, 'organization__name'] = 'Sub-Totals'
     total = pd.DataFrame(merged.sum(axis=0)).transpose()
     total.at[0, 'organization__name'] = 'Statewide Obligation Totals'
     df = pd.concat([merged[merged['organization__name'] != 'Sound Transit'], subtotal, merged[merged['organization__name'] == 'Sound Transit'], total], axis = 0).set_index('organization__name')
     df['Total Annual Expenses'] = df[['Demand Response', 'Fixed Route', 'All Rail Modes', 'Route Deviated', 'Vanpool',
       'Other-Expenditures', 'Debt Service', 'Capital Expenses']].sum(axis =1)
     df = df.rename(columns = {'Other-Expenditures': 'Other', 'Depreciation (Not included in Total Expenditures)':'Depreciation'})
     df = df.reindex(columns = ['Fixed Route', 'Route Deviated', 'Demand Response', 'Vanpool', 'All Rail Modes', 'Debt Service', 'Other', 'Capital Expenses', 'Total Annual Expenses', 'Depreciation'])
     return df











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
     df['Passenger Trips/Revenue Mile'] = df['Passenger Trips']/ df['Revenue Vehicle Miles']
     df['Revenue Hours/FTE'] = df['Revenue Vehicle Hours']/df['Employees - FTEs']
     df['Operating Expenses/Revenue Hour'] = df['Operating Expenses']/df['Revenue Vehicle Hours']
     df['Operating Expenses/ Revenue Mile'] = df['Operating Expenses']/df['Revenue Vehicle Miles']
     df['Operating Expenses/Passenger Trip'] = df['Operating Expenses']/df['Passenger Trips']
     df['Farebox Recovery Ratio'] = df['Farebox Revenues']/df['Operating Expenses']
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
         sums['Passenger Trips/Revenue Hour'] = sums['Passenger Trips']/sums['Revenue Vehicle Hours']
         sums['Passenger Trips/Revenue Mile'] = sums['Passenger Trips']/ sums['Revenue Vehicle Miles']
         sums['Revenue Hours/FTE'] = sums['Revenue Vehicle Hours'] / sums['Employees - FTEs']
         sums['Operating Expenses/Revenue Hour'] = sums['Operating Expenses']/sums['Revenue Vehicle Hours']
         sums['Operating Expenses/ Revenue Mile'] = sums['Operating Expenses'] / sums['Revenue Vehicle Miles']
         sums['Operating Expenses/Passenger Trip'] = sums['Operating Expenses'] / sums['Passenger Trips']
         sums['Farebox Recovery Ratio'] = sums['Farebox Revenues'] / sums['Operating Expenses']

     else:
         sums = df[df.classification == category][['Revenue Vehicle Hours', 'Total Vehicle Hours', 'Revenue Vehicle Miles', 'Total Vehicle Miles','Passenger Trips', 'Employees - FTEs', 'Operating Expenses', 'Farebox Revenues']].sum()
         sums['Passenger Trips/Revenue Hour']= sums['Passenger Trips']/sums['Revenue Vehicle Hours']
         sums['Passenger Trips/Revenue Mile'] = sums['Passenger Trips']/ sums['Revenue Vehicle Miles']
         sums['Revenue Hours/FTE'] = sums['Revenue Vehicle Hours']/ sums['Employees - FTEs']
         sums['Operating Expenses/Revenue Hour'] = sums['Operating Expenses']/sums['Revenue Vehicle Hours']
         sums['Operating Expenses/ Revenue Mile'] = sums['Operating Expenses']/sums['Revenue Vehicle Miles']
         sums['Operating Expenses/Passenger Trip'] = sums['Operating Expenses'] / sums['Passenger Trips']
         sums['Farebox Recovery Ratio'] = sums['Farebox Revenues']/ sums['Operating Expenses']
         sums.to_csv(r'I:\Public_Transportation\Data_Team\PT_Summary\2019\Transits\Statewide\test.csv')
     sums = pd.DataFrame(sums)
     changeddf = sums.transpose()
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


def generate_performance_measure_table(metric, years, big):
    heading_list = [metric] + years + ['One Year Change (%)']
    if big == 'sound':
        if len(metric) == 2:
             df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years,reported_value__isnull=False).exclude( organization_id__in = [15,33]).values('year', 'transit_mode__rollup_mode').annotate(
            reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric[0]))/ Sum('reported_value', filter = Q(transit_metric__name = metric[1]))))
        else:
             df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years, reported_value__isnull=False).exclude( organization_id__in = [15,33]).values('year', 'transit_mode__rollup_mode').annotate(reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric))))
    else:
         if len(metric) == 2:
             df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years,reported_value__isnull=False).values('year', 'transit_mode__rollup_mode').annotate(
            reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric[0]))/ Sum('reported_value', filter = Q(transit_metric__name = metric[1]))))
         else:
            df = read_frame(transit_data.objects.filter(organization__summary_organization_classifications=6, year__in=years, reported_value__isnull=False).values('year', 'transit_mode__rollup_mode').annotate(reported_value=Sum('reported_value', filter=Q(transit_metric__name=metric))))
    df = df.dropna(thresh=3)
    df = df.pivot(index = 'transit_mode__rollup_mode', columns = 'year', values= 'reported_value')
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
    heading = [metric] + years + ['percent_change']
    df.columns = heading_list
    return df


def create_statewide_revenue(year, big):
    from . models import transit_data
    if big == 'sound':
        df = revenue.objects.filter(organization_id__summary_organization_classifications_id=6, year__in=(2014, 2015, 2016, 2017, 2018, 2019)).exclude(revenue_source__name__in = ['Land Bank Agreement & Credits', 'dec_res', 'inc_res']).exclude( organization_id__in = [15,33]).values('revenue_source__government_type','year').annotate(reported_value=Sum('reported_value'))
        transit_data = transit_data.objects.filter(organization_id__summary_organization_classifications_id=6,year__in=(2014, 2015, 2016, 2017, 2018, 2019), transit_metric_id = 10).exclude( organization_id__in = [15,33]).values('year').annotate(reported_value = Sum('reported_value'))
    else:
        df = revenue.objects.filter(organization_id__summary_organization_classifications_id=6,year__in=(2014, 2015, 2016, 2017, 2018, 2019)).exclude(
            revenue_source__name__in=['Land Bank Agreement & Credits', 'dec_res', 'inc_res']).values('revenue_source__government_type', 'year').annotate(reported_value=Sum('reported_value'))
        transit_data = transit_data.objects.filter(organization_id__summary_organization_classifications_id=6,
                                                   year__in=(2014, 2015, 2016, 2017, 2018, 2019),
                                                   transit_metric_id=10).values('year').annotate(
            reported_value=Sum('reported_value'))
    df = read_frame((df))
    transit_df = read_frame(transit_data)
    transit_df['revenue_source__government_type'] = 'Farebox Revenues'
    df = df.pivot(index = 'revenue_source__government_type', columns = 'year', values = 'reported_value')
    transit_df = transit_df.pivot(index = 'revenue_source__government_type', columns = 'year', values = 'reported_value')
    df = pd.concat([df, transit_df], axis=0)
    df = df.reset_index()
    df = df.rename(columns={'revenue_source__government_type': 'rev'})
    df.loc[5, :] = df[df['rev'].isin(['Local', 'Other', 'Farebox Revenues'])].sum(axis=0)
    df.at[5, 'rev'] = 'Local Revenues'
    total = ['Local Revenues', 'State', 'Federal']
    df.loc[6, :] = df[df['rev'].isin(total)].sum(axis=0)
    df.at[6, 'rev'] = 'Total'
    df = df[df.rev.isin(['Local Revenues', 'State', 'Federal', 'Total'])]
    df = df.set_index('rev')
    reindex_list = ['Local Revenues', 'State', 'Federal', 'Total']
    df = df.reindex(reindex_list)
    df = df.reset_index()
    df = df.rename(columns = {'rev':'TotalRevenues'})
    df.TotalRevenues = df.TotalRevenues.apply(lambda x: x + ' Revenues' if 'Revenues' not in x else x)
    return df
