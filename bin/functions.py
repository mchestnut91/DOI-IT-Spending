import pandas as pd
import numpy as np
import textwrap


columns = ['UII','bureau_name','portfolio_part','investment_title','fea_service_area','FY18','FY19',
           'FY20','date']
old_columns = ['Unique Investment Identifier','Bureau Name','Part Of IT Portfolio','Investment Title',
              'FEA BRM Services - Primary service area','Total IT Spending FY2018 (PY) ($ M)',
              'Total IT Spending FY2019 (CY) ($ M)','Total IT Spending FY2020 (BY) ($ M)','Updated Date']

abbrevs = ['DOI', 'BLM', 'BOEM', 'OSMRE', 'BR', 'USGS', 'FWS', 'BSEE', 'NPS', 'BIA','DO','SOL','OST']

def rename(part):
    if part == '01 - Mission Delivery':
        return 'Mission Delivery'
    elif part == '02 - Administrative Services and Support Systems':
        return 'Admin Services'
    else:
        return 'IT'

def clean_data(df,columns,old_columns,bureaus):
    df = df[old_columns]
    df.columns=columns
    df['portfolio_part'] = df['portfolio_part'].apply(rename)
    df['trimmed_investment_title'] = df['investment_title'].str.split('-',1).str[1]
    df['trimmed_fea_service_area'] = df['fea_service_area'].str.split('-',1).str[1]
    df['bureau_abbrev'] = df['bureau_name'].apply(assign_abbrev,args=(bureaus,))
    return df
    
def assign_colors(portfolio):
    if portfolio == 'IT':
        return '#a6cee3'
    elif portfolio == 'Admin Services':
        return '#1f78b4'
    else:
        return '#b2df8a'

def aggregate_for_sankey(df):
    edges = df.groupby(['bureau_name','portfolio_part']).sum().reset_index()
    edges['label'] = edges['bureau_name'].map(str) + ": " + edges['portfolio_part']
    edges['color'] = '#262C46'
    edges['link_color'] = edges['portfolio_part'].apply(assign_colors)
    return edges

def aggregate_for_donut(df):
    donut=df.groupby(['bureau_name','bureau_abbrev','portfolio_part','trimmed_fea_service_area']).sum().reset_index()
    return donut

def get_options(bureaus):
    options=[]
    [options.append({'label': i, 'value': i}) for i in bureaus]
    return options

def wrap_legend_text(series):
    return ['<br>'.join(textwrap.wrap(string, width=40)) for string in series]

def wrap_title_text(string):
    return '<br>'.join(textwrap.wrap(string, width=60))

def assign_abbrev(bureau,bureaus):
    dicty = {}
    for k,v in zip(bureaus,abbrevs):
        dicty[k]=v
    return dicty[bureau]