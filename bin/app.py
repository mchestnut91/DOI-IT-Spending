import pandas as pd
import numpy as np
import functions as fn
from functions import columns, old_columns
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from bokeh.palettes import Set3, Paired

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

#Read data in
data = pd.read_csv('../fixtures/data.csv')

#Get list of bureaus
bureaus = pd.unique(data['Bureau Name']).tolist()
print(bureaus)
bureau_dropdown_options = fn.get_options(bureaus)

#Clean data
df = fn.clean_data(data, columns, old_columns,bureaus=bureaus)
edges = fn.aggregate_for_sankey(df)
slices = fn.aggregate_for_donut(df)

markdown_text = '''
### Mapping Department of Interior Spending 
'''

app.layout = html.Div([
    html.Div([
        dcc.Markdown(children=markdown_text)
    ],style={"text-align": "center"},
    className="row"),
    
    html.Div([
        html.Div([
            html.Label('Year:'),
            dcc.Dropdown(
                id='fy-dropdown',
                options=[
                    {'label': 'FY18', 'value': 'FY18'},
                    {'label': 'FY19', 'value': 'FY19'},
                    {'label': 'FY20', 'value': 'FY20'}
                ],
                value='FY18'
            )
        ],className="two columns"),

        html.Div([

            html.Label('Bureau:'),
            dcc.Dropdown(
                id='bureau-dropdown',
                options=bureau_dropdown_options,
                value='Department of the Interior'
            )
        ],className="four columns")

    ],className="row"),

    html.Div([
        html.Div([
            html.Div([
                dcc.Graph(id='sankey')
            ],className="six columns"),
            html.Div([
                dcc.Graph(id='donut')
            ],className="six columns")
        ],className="row"),
        html.Div([
            dcc.Graph(id='horizontal-bars')
        ],className="row")
    ],className="twelve columns")

],className ="twelve columns")

@app.callback(
    Output('sankey','figure'),
    [Input('fy-dropdown', 'value')]
)

def plot_sankey(selected_year):
    filtered_df = edges[['bureau_name','portfolio_part','color','label','link_color',selected_year]]
    sorted = filtered_df.sort_values(selected_year,ascending=False)

    portfolio=sorted['portfolio_part'].tolist()
    bureau=sorted['bureau_name'].tolist()
    unique_values=pd.unique(pd.concat((sorted['bureau_name'],sorted['portfolio_part']),axis=0)).tolist()
    portfolio_indices=[unique_values.index(i) for i in portfolio] 
    bureau_indices=[unique_values.index(i) for i in bureau]

    data_trace = dict(
        type='sankey',
        domain=dict(
            x=[0,1],
            y=[0,1]
        ),
        orientation="h",
        valueformat=".0f",
        node=dict(
            pad = 10,
            thickness=20,
            line=dict(
                color="black",
                width=0.5
            ),
            hovertemplate="%{label} " + selected_year,
            # value="selected_year: ${value:$.2f}",
            label= unique_values,
            color = sorted['color']
        ),
        link=dict(
            source=bureau_indices,
            target=portfolio_indices,
            value=sorted[selected_year].dropna(axis=0,how='any'),
            color=sorted['link_color']
        )
    )
    layout= dict(
        title=dict(
            text=fn.wrap_title_text('All Bureaus Spending by Portfolio Part ' + selected_year + ' (In Millions)'),
            font=dict(
                size=16
            )
        ),
        height=500,
        width=600,
        margin = dict(l = 10, r = 0, b = 10, t = 50, pad = 2),
        font=dict(
            size=10
        ),
    )

    return {
        'data': [data_trace],
        'layout': layout
    }

@app.callback(
    Output('horizontal-bars','figure'),
    [Input('bureau-dropdown','value'),
    Input('fy-dropdown', 'value')]
)
def update_bars(bureau,fy):
    filtered_df = df[['bureau_name','portfolio_part','trimmed_investment_title',fy]]
    filtered_df = filtered_df[filtered_df['bureau_name']==bureau]
    filtered_df = filtered_df[filtered_df[fy]>0.00]

    #Sort and return top 10 based on FY values
    top10 = filtered_df.nlargest(10,fy)
    top10['color'] = top10['portfolio_part'].apply(fn.assign_colors)

    data=[]
    for i in range(0, len(pd.unique(top10['portfolio_part']))):
        data.append(go.Bar(
            x= top10[fy][top10['portfolio_part'] == pd.unique(top10['portfolio_part'])[i]],
            y= top10['trimmed_investment_title'][top10['portfolio_part'] == pd.unique(top10['portfolio_part'])[i]],
            name= pd.unique(top10['portfolio_part'])[i],
            orientation= 'h',
            marker=dict(
                color = top10['color'][top10['portfolio_part'] == pd.unique(top10['portfolio_part'])[i]]
            )   
        ))
            
    layout = go.Layout(
        title = go.layout.Title(
            text='Top 10 ' + str(bureau) + ' Investments in ' + str(fy),
        ),
        margin = dict(l = 450, r = 20, b = 50, t = 50, pad = 2),
        xaxis=dict(
            title=str(fy) +' Spending (In Millions)'),
        showlegend=True
    )

    return {
    'data': data,
    'layout': layout
    }

@app.callback(
    Output('donut','figure'),
    [Input('bureau-dropdown','value'),
    Input('fy-dropdown', 'value')]
)
def update_donut(bureau,fy):
    filtered_df = slices[['bureau_name','bureau_abbrev','trimmed_fea_service_area',fy]]
    filtered_df = filtered_df[filtered_df['bureau_name']==bureau]
    filtered_df = filtered_df[filtered_df[fy]>0.00]
    
    #Sort and return top 10 based on FY values
    top10 = filtered_df.nlargest(10,fy)
    data = dict(
        values=top10[fy],
        labels=fn.wrap_legend_text(top10['trimmed_fea_service_area']),
        name=top10['trimmed_fea_service_area'],
        hoverinfo="label+value+name",
        hole=.4,
    
        type="pie",
        marker=dict(
            colors=Paired[10]
        )
    )
    layout = dict(
        title=fn.wrap_title_text(top10.iloc[0]['bureau_abbrev'] + ' FEA Service Breakdown ' +fy),
        legend=dict(
            x=-1.02,y=1.02,xanchor='left',yanchor='top',font=dict(
                size=11)
        ),
        annotations=[dict(
            font=dict(
                size=20
            ),
            showarrow=False,
            text=top10.iloc[0]['bureau_abbrev'],
            x=.49,
            y=0.5
        )],
        margin = dict(l = 0, r = 20, b = 10, t = 60, pad = 0),
    )
    return {
    'data':[data],
    'layout':layout
    }

if __name__ == "__main__":
    app.run_server(debug=True)
