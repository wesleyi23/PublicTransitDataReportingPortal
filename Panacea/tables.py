from Panacea.models import revenue, transit_data, service_offered, transit_mode, fund_balance, expense, depreciation, organization, stylesheets, expense_source, revenue_source
import pandas as pd
import numpy as np
from django_pandas.io import read_frame
from django.db.models import Sum












def calculate_percent_change(data1, data2):
    try:
        percent = (data2 - data1)/data1
        percent = percent*100
    except ZeroDivisionError:
        percent = 100.00
    return percent




def index_others(df):
    index_list = df[df['revenue_source'].isin(['Other Operating Sub-Total','Other-Advertising', 'Other-Interest', 'Other-Gain (Loss) on Sale of Assets','Other-MISC'])].index
    df.loc[index_list, 'role'] = 'other_indent'
    index_list = df[df['revenue_source'].isin(['Other Operating Sub-Total'])].index
    df.loc[index_list, 'role'] = 'subtotal'
    return df

def percent_change(df):
    df['percent_change'] = ((df['year3'] - df['year2']) / df['year2']) * 100
    df = df.fillna('-')
    df = df.replace(np.inf, 100.00)
    return df

def build_total_funds_by_source(years, user_org_id):
    local = read_frame(revenue.objects.filter(organization_id__in = user_org_id, year__in = years, revenue_source__government_type = 'Local', reported_value__isnull=False).values('year').annotate(Local_Revenues = Sum('reported_value')))
    state = read_frame(revenue.objects.filter(organization_id__in =user_org_id, year__in=years, revenue_source__government_type='State', reported_value__isnull=False).values('year').annotate(State_Revenues = Sum('reported_value')))
    fed = read_frame(revenue.objects.filter(organization_id__in =user_org_id, year__in=years,revenue_source__government_type='Federal', reported_value__isnull=False).values('year').annotate(Federal_Revenues=Sum('reported_value')))
    df = pd.concat([local.set_index('year'), state.set_index('year'), fed.set_index('year')], axis = 1)
    df = df.transpose()
    if df.empty == True:
        return pd.DataFrame()
    df = df.dropna(thresh=len(df.columns))
    df = df.reset_index()
    try:
        df.columns = ['revenue_source', 'year1', 'year2', 'year3']
    except ValueError:
        df = df.set_index('index')
        df = fill_empty_columns(df, years, 'expense')
        df = df.reset_index()
        df.columns = ['revenue_source', 'year1', 'year2', 'year3']
    df = df.set_index('revenue_source')
    total_list = list(df.sum(axis = 0))
    df = df.reset_index()
    df['role'] = 'body'
    total_list = ['Total Revenues (all sources)'] + total_list + ['subtotal']
    df = df.append(dict(zip(df.columns.tolist(), total_list)), ignore_index = True)
    df = percent_change(df)
    heading_list = ['Revenues', '', '', '', 'heading', '']
    df = add_a_list_to_a_dataframe(df, heading_list)
    df['revenue_source'] = df['revenue_source'].str.replace('_', ' ')
    investmentdf = build_investment_table(years, user_org_id)
    df = pd.concat([df, investmentdf], axis=0)
    df.revenue_source = df.revenue_source.str.replace('_', ' ')
    return df


def build_investment_table(years, user_org_id):
    operating = read_frame(transit_data.objects.filter(organization_id__in = user_org_id, year__in=years, transit_metric__name= 'Operating Expenses', reported_value__isnull=False).values('year').annotate(Operating_Investment = Sum('reported_value')))
    local_cap = read_frame(revenue.objects.filter(organization_id__in = user_org_id, year__in=years, revenue_source__name__in= ['Local Capital Funds', 'Other Local Capital'], reported_value__isnull=False).values('year').annotate(Local_Capital_Investment = Sum('reported_value')))
    state_cap = read_frame(revenue.objects.filter(organization_id__in=user_org_id, year__in=years, revenue_source__government_type='State', revenue_source__funding_type='Capital', reported_value__isnull=False).values('year').annotate(State_Capital_Investment = Sum('reported_value')))
    federal_cap = read_frame(revenue.objects.filter(organization_id__in = user_org_id, year__in = years, revenue_source__government_type='Federal', revenue_source__funding_type='Capital', reported_value__isnull = False).values('year').annotate(Federal_Capital_Investment = Sum('reported_value')))
    other_cap = read_frame(expense.objects.filter(organization_id__in = user_org_id, year__in = years, expense_source__name__in= ['Other-Expenditures', 'Interest', 'Principal'], reported_value__isnull=False).values('year').annotate(Other_Capital_Investment = Sum('reported_value')))
    df = pd.concat([operating.set_index('year'), local_cap.set_index('year'), state_cap.set_index('year'), federal_cap.set_index('year'), other_cap.set_index('year')], axis=1)
    df = df.transpose()
    df = df.dropna(thresh=len(df.columns))
    df = df.reset_index()
    try:
        df.columns = ['revenue_source', 'year1', 'year2', 'year3']
    except ValueError:
        df = df.set_index('index')
        df = fill_empty_columns(df, years, 'expense')
        df = df.reset_index()
        df.columns = ['revenue_source', 'year1', 'year2', 'year3']
    df = df.set_index('revenue_source')
    total_list = list(df.sum(axis=0))
    df = df.reset_index()
    df['role'] = 'body'
    total_list = ['Total Investment'] + total_list + ['subtotal']
    df = df.append(dict(zip(df.columns.tolist(), total_list)), ignore_index=True)
    df = percent_change(df)
    heading_list = ['Investments', '', '', '', 'heading', '']
    df = add_a_list_to_a_dataframe(df, heading_list)
    df['revenue_source'] = df['revenue_source'].str.replace('_', ' ')
    return df


def get_farebox_and_vp_revenues(years, user_org_id, classification):
    '''calculates_total farebox revenues and vanpool revenue for revenue tables'''
    farebox_modes = list(service_offered.objects.filter(organization_id__in=user_org_id).values_list('transit_mode_id', flat=True))
    farebox_modes = [i for i in farebox_modes if i != 3] #filtering out the vanpool so it is not double counted
    farebox = transit_data.objects.filter(organization_id__in=user_org_id, year__in=years, transit_metric__name='Farebox Revenues',transit_mode_id__in= farebox_modes).values('year').annotate(reported_value = Sum('reported_value'))
    fares = read_frame(farebox)
    fares['revenue_source'] = 'Farebox Revenues'
    if str(classification) == 'Transit':
        vanpool = transit_data.objects.filter(organization_id__in=user_org_id, year__in=years,
                                          transit_metric__name='Farebox Revenues',
                                          transit_mode_id =3).values('year').annotate(reported_value=Sum('reported_value'))
        vanpool = read_frame(vanpool)
        vanpool['revenue_source'] = 'Vanpooling Revenue'
        fares = pd.concat([fares, vanpool], axis=0)
    return fares

def other_operating_sub_total(years, user_org_id):
    '''calculates the other operating subtotal'''
    #TODO add different ferry revenues in here that generate other op subtotal
    other_op = revenue.objects.filter(organization_id__in=user_org_id, year__in=years, revenue_source__name__in= ['Other-Advertising',
        'Other-Gain (Loss) on Sale of Assets', 'Other-Interest', 'Other-MISC', 'Other - Other Revenues']).values('year').annotate(reported_value = Sum('reported_value'))
    other_op = read_frame(other_op)
    other_op['revenue_source'] = 'Other Operating Sub-Total'
    return other_op

def add_fund_types_and_headings(df):
    '''this function '''
    government_type_list = []
    funding_type_list = []
    for revenue in df.revenue_source.tolist():
        output = revenue_source.objects.filter(name = revenue).values('government_type', 'funding_type')
        try:
            government_type_list.append(output[0]['government_type'])
            funding_type_list.append(output[0]['funding_type'])
        except:
            government_type_list.append('')
            funding_type_list.append('')
    df['government_type'] = government_type_list
    df['funding_type'] = funding_type_list
    return df



def make_headings(df, classification):
    '''function that adds relevant headings to table'''
    total_heading = list(set(zip(df['government_type'], df['funding_type'])))
    if ('State', 'Capital') in total_heading:
        mode_list = ['State Capital Grant Revenues', '', '', '', '', 'heading', '', '']
        df = add_a_list_to_a_dataframe(df, mode_list)
    if ('Federal', 'Capital') in total_heading:
        mode_list = ['Federal Capital Grant Revenues', '', '', '', '', 'heading', '', '']
        df = add_a_list_to_a_dataframe(df, mode_list)
    if ('Other', 'Expenditures') in total_heading and str(classification) == 'Ferry':
        mode_list = ['Other Expenditures', '', '', '', '', 'heading', '', '']
        df = add_a_list_to_a_dataframe(df, mode_list)
    if ('Local', 'Capital') in total_heading and str(classification) == 'Ferry':
        mode_list = ['Local Capital Expenditures', '', '', '', '', 'heading', '', '']
        df = add_a_list_to_a_dataframe(df, mode_list)
    mode_list = ['Operating Related Revenues', '', '', '', '', 'heading', '', '']
    df = add_a_list_to_a_dataframe(df, mode_list)
    return df

def add_a_list_to_a_dataframe(df, added_list):
    columns_list = df.columns.tolist()
    intermediate_df = pd.DataFrame(dict(zip(columns_list, added_list)), index=[0])
    df = pd.concat([intermediate_df, df], axis=0).reset_index(drop=True)
    return df

def calculate_subtotals(df, years, subtotal_value):
    df = df[years]
    res = list(df.sum(axis=0)[years])
    percent_change = calculate_percent_change(res[1], res[2])
    result_list = [subtotal_value] + res + [percent_change] + ['subtotal','', '']
    return result_list

def make_subtotals(df,years, classification):
    '''function to add up and grab relevant subtotals for revenue table'''
    total_heading = list(set(zip(df['government_type'], df['funding_type'])))
    if ('State', 'Capital') in total_heading:
        filtered_df = df[(df['government_type'] == 'State') & (df['funding_type'] == 'Capital')]
        result_list = calculate_subtotals(filtered_df, years, 'Total State Capital')
        df = add_a_list_to_a_dataframe(df, result_list)
    if ('Federal', 'Capital') in total_heading:
        filtered_df = df[(df['government_type'] == 'Federal') & (df['funding_type'] == 'Capital')]
        result_list = calculate_subtotals(filtered_df, years, 'Total Federal Capital')
        df = add_a_list_to_a_dataframe(df, result_list)
    if ('Local', 'Capital') in total_heading and str(classification) == 'Ferry':
        filtered_df = df[(df['government_type'] == 'Local') & (df['funding_type'] == 'Capital')]
        result_list = calculate_subtotals(filtered_df, years, 'Total Local Capital')
        df = add_a_list_to_a_dataframe(df, result_list)
    if ('Other', 'Expenditures') in total_heading and str(classification) == 'Ferry':
        filtered_df = df[(df['government_type'] == 'Other') & (df['funding_type'] == 'Expenditures')]
        result_list = calculate_subtotals(filtered_df, years, 'Total Other Expenditures')
        df = add_a_list_to_a_dataframe(df, result_list)
    filtered_df = df[df['funding_type'] == 'Operating']
    result_list = calculate_subtotals(filtered_df, years, 'Total (Excludes Capital Revenue)')
    df = add_a_list_to_a_dataframe(df, result_list)
    return df


def build_community_provider_revenue_table(years, user_org_id):
    funding_order = [('Operating', ['State', 'Local', 'Other']), ('Capital', ['State', 'Local', 'Other']), ('Operating', ['Federal']), ('Capital', ['Federal'])]
    count = 0
    for funding in funding_order:
        revenue_data = revenue.objects.filter(organization_id__in=user_org_id, year__in = years, revenue_source__government_type__in=funding[1], revenue_source__funding_type=funding[0]).values('revenue_source__name', 'reported_value', 'year', 'revenue_source_id')
        df = read_frame(revenue_data)
        df = df.pivot(index='revenue_source__name', columns='year', values='reported_value').fillna(0)
        subtotal_list = ['Sub-Total'] +list(df.sum(axis=0))
        df = df.reset_index()
        df = add_a_list_to_a_dataframe(df, subtotal_list)
        print(df)


def build_revenue_table(years, user_org_id, classification):
    data_revenue = revenue.objects.filter(organization_id__in = user_org_id, year__in = years)
    df = read_frame(data_revenue)
    print(df)
    df = df[df.reported_value.notna()][['revenue_source', 'reported_value', 'year']]
    if df.empty == True:
        return df
    fares = get_farebox_and_vp_revenues(years, user_org_id, classification)
    other_op = other_operating_sub_total(years, user_org_id)
    finaldf = pd.concat([df, fares, other_op], axis=0)
    print(finaldf)
    finaldf = finaldf.pivot(index='revenue_source', columns='year', values='reported_value').fillna(0)
    finaldf = finaldf.reset_index()
    try:
        finaldf.columns = ['revenue_source', 'year1', 'year2', 'year3']
    except ValueError:
        finaldf = finaldf.set_index('revenue_source')
        finaldf = fill_empty_columns(finaldf, years, 'revenue')
        finaldf = finaldf.reset_index()
        finaldf.columns = ['revenue_source', 'year1', 'year2', 'year3']
    finaldf = percent_change(finaldf)
    finaldf['role'] = 'body'
    finaldf = add_fund_types_and_headings(finaldf)
    finaldf = make_headings(finaldf, classification)
    cols = ['year1', 'year2', 'year3']
    finaldf = make_subtotals(finaldf, cols, classification)
    revenue_list = call_stylesheets(classification, 'revenue')
    finaldf = finaldf.set_index('revenue_source')
    finaldf = finaldf.reindex(revenue_list).dropna(thresh=4)
    finaldf = finaldf.reset_index()
    finaldf = index_others(finaldf)
    finaldf.columns = ['revenue_source', 'year1', 'year2', 'year3', 'percent_change', 'role', 'government_type', 'funding_type']
    if str(classification) in ['Transit', 'Tribe']:
        expensedf = build_expense_table(years, user_org_id, classification)
        finaldf = pd.concat([finaldf, expensedf], axis = 0)
    return finaldf

#TODO need some backstop functionality for the fact that for any given mode or expense, possibility that there's no previous data

def fill_empty_columns(df, years, table_type):
    for year in years:
        if year not in df.columns.tolist():
            if table_type in ['revenue', 'expense']:
                df[year] = 0
            else:
                df[year] = np.nan
    df = df[sorted(df)]
    return df

def pull_headings(df):
    headings_list = df['heading'].unique().tolist()
    return headings_list

def add_headings(df, heading_list):
    '''function for taking a generated list of headings and adding them to the result dataframe'''
    for heading in heading_list:
        ls_heading = [heading, '', '', '', '', 'heading']
        df = add_a_list_to_a_dataframe(df, ls_heading)
    return df

def make_expense_subtotals(df, years):
    expenditure_dic = {'Total Local Capital': ['Local Capital Funds', 'Other Local Capital'], 'Total Debt Service': ['Interest', 'Principal'], 'Total': ['General Fund', 'Unrestricted Cash and Investments', 'Operating Reserve', 'Working Capital', 'Capital Reserve Funds', 'Contingency Reserve', 'Debt Service Funds', 'Insurance Funds', 'Other'], 'Total Other Expenditures': ['Lease and Rental Agreements', 'Other Reconciling Items']}
    for key, value in expenditure_dic.items():
        if len(df[df.revenue_source.isin(value)]) > 0:
            result_list = calculate_subtotals(df[df.revenue_source.isin(value)], years, key)
            df = add_a_list_to_a_dataframe(df, result_list)
    return df

def reindex_table_expense(df, user_org_id, classification):
    df = df.set_index('revenue_source')
    if str(classification) in ['Transit', 'Tribe']:
        expense_index = stylesheets.objects.filter(transit_expense__isnull=False).values_list('transit_expense', flat=True)
    elif str(classification) == 'Ferry':
        expense_index = stylesheets.objects.filter(transit_expense__isnull=False).values_list('ferry_expense',flat=True)
    df = df.reindex(expense_index).dropna(thresh = 1)
    df = df.reset_index()
    return df


def build_expense_table(years, user_org_id, classification):
    from .models import fund_balance
    from .models import depreciation
    data_expense = expense.objects.filter(organization_id__in = user_org_id, year__in = years, reported_value__isnull= False).values('reported_value', 'year', 'expense_source_id__name', 'expense_source_id__heading')
    fund_balance = fund_balance.objects.filter(organization_id__in = user_org_id, year__in = years, reported_value__isnull=False).values('reported_value', 'year', 'fund_balance_type__name', 'fund_balance_type__heading')
    depreciation = depreciation.objects.filter(organization_id__in = user_org_id, year__in = years)
    df_expense = read_frame(data_expense)
    fund_balance = read_frame(fund_balance)
    depreciation = read_frame(depreciation)
    df_expense = df_expense.rename(columns ={'expense_source_id__name': 'revenue_source', 'expense_source_id__heading':'heading'})
    fund_balance = fund_balance.rename(columns = {'fund_balance_type__name': 'revenue_source', 'fund_balance_type__heading': 'heading'})
    if len(depreciation) > 0:
        depreciation['revenue_source'] = 'Depreciation'
        depreciation['heading'] = 'Other Expenditures'
    df = pd.concat([fund_balance, df_expense, depreciation], axis = 0)
    headings_list = pull_headings(df)
    df = df.pivot(index='revenue_source', columns='year', values='reported_value').fillna(0)
    df = df.reset_index()
    try:
        df.columns = ['revenue_source', 'year1', 'year2', 'year3']
    except ValueError:
        df = df.set_index('revenue_source')
        df = fill_empty_columns(df, years, 'expense')
        df = df.reset_index()
        df.columns = ['revenue_source', 'year1', 'year2', 'year3']
    df = percent_change(df)
    df['role'] = 'body'
    df = add_headings(df, headings_list)
    cols = ['year1', 'year2', 'year3']
    df = make_expense_subtotals(df, cols)
    df = reindex_table_expense(df, user_org_id, classification)
    df['government_type'] = ''
    df['funding_type'] = ''
    df.columns = ['revenue_source', 'year1', 'year2', 'year3', 'percent_change', 'role', 'government_type', 'funding_type']
    return df


def call_stylesheets(classification, type):
    '''associated function for creating stylesheets for the Summary tables '''
    classification = str(classification)
    if classification == 'Transit' and type == 'data':
        return list(stylesheets.objects.filter(transit_data__isnull=False).values_list('transit_data', flat=True))
    elif classification == 'Tribe' and type == 'data':
        return list(stylesheets.objects.filter(transit_data__isnull=False).values_list('transit_data', flat=True))
    elif classification == 'Transit' and type == 'revenue':
        return list(stylesheets.objects.filter(transit_revenue__isnull=False).values_list('transit_revenue', flat=True))
    elif classification == 'Tribe' and type == 'revenue':
        return list(stylesheets.objects.filter(transit_revenue__isnull=False).values_list('transit_revenue', flat=True))
    elif classification == 'Ferry' and type == 'data':
        return list(stylesheets.objects.filter(ferry_data__isnull=False).values_list('ferry_data', flat=True))
    elif classification == 'Community provider' and type == 'data':
        return list(stylesheets.objects.filter(cp_data__isnull=False).values_list('cp_data', flat=True))
    elif classification == 'Community provider' and type == 'federal':
        return list(stylesheets.objects.filter(cp_revenue_federal__isnull=False).values_list('cp_revenue_federal', flat=True))
    elif classification == 'Community provider' and type == 'revenue':
        return list(stylesheets.objects.filter(cp_revenue_source__isnull=False).values_list('cp_revenue_source', flat=True))
    elif classification == 'Ferry' and type == 'revenue':
        return list(stylesheets.objects.filter(ferry_revenue__isnull=False).values_list('ferry_revenue', flat=True))


def build_operations_data_table(years, org_id, classification):
    '''function for pulling all available data within certain years for a transit and pushing it out to a summary sheet'''
    from .models import transit_data
    services_offered = service_offered.objects.filter(organization_id__in=org_id, service_mode_discontinued=False).values('administration_of_mode','transit_mode_id').distinct()
    transitdata = transit_data.objects.filter(organization_id__in=org_id, year__in=years).values('administration_of_mode', 'transit_mode', 'year', 'transit_metric').annotate(reported_value = Sum('reported_value'))
    count = 0
    if str(classification) == 'Community provider':
        services_offered = list(services_offered) + ['all']
    # for loop of services offered builds out a dataframe for the table
    if list(services_offered) == []:
        return pd.DataFrame()
    for service in services_offered:
        if service == 'all':
            filter  = transit_data.objects.filter(organization_id__in = org_id, year__in = years).values('year', 'transit_metric__name').annotate(reported_value = Sum('reported_value'))
        else:
            filter = transitdata.filter(administration_of_mode=service['administration_of_mode'],transit_mode_id=service['transit_mode_id'])
        df = read_frame(filter)
        if df.empty == True:
            continue
        else:
            df = df[df.reported_value.notna()]
            df = df.rename(columns = {'transit_metric__name': 'transit_metric'})
            # pivot method here turns transit metics into the index and years into columns
            df = df.pivot(index='transit_metric', columns='year', values='reported_value').fillna(0)
            order_list = call_stylesheets(classification, 'data')
            # orders the index based on Summary styling
            df = df.reindex(order_list).dropna()
            df = df.reset_index()
            # adds a percent change column
            try:
                df.columns = ['transit_metric', 'year1', 'year2', 'year3']
            except ValueError:
                df = df.set_index('transit_metric')
                df = fill_empty_columns(df, years, 'data')
                df = df.reset_index()
                df.columns = ['transit_metric', 'year1', 'year2', 'year3']
            try:
                df['percent_change'] = ((df['year3'] - df['year2']) / df['year2'])* 100
                df['percent_change'] = df['percent_change'].replace(np.inf, 100.00)
            except IndexError:
                df['percent_change'] = np.nan
            df['role'] = 'body'
            if str(classification) == 'Ferry':
                mode_name = 'Passenger Ferry Services'
            elif str(classification) == 'Community provider':
                if service == 'all':
                    mode_name = 'Total of All Service Modes'
                else:
                    mode_name = '{} Services'.format(transit_mode.objects.filter(id=service['transit_mode_id']).values('name')[0]['name'])
            else:
                mode_name = '{} ({})'.format(transit_mode.objects.filter(id=service['transit_mode_id']).values('name')[0]['name'], service['administration_of_mode'])
            mode_list = [mode_name, '', '', '', '', 'heading']
            mode_list_df = pd.DataFrame(dict(zip(df.columns.tolist(), mode_list)), index=[0])
            df = pd.concat([mode_list_df, df]).reset_index(drop=True)
            if count == 0:
                enddf = df
                count += 1
            else:
                enddf = pd.concat([enddf, df], axis=0)
    if df.empty == True:
        return df
    else:
        enddf = enddf.fillna('-')
    return enddf
