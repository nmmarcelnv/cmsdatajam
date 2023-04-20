#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 15 11:03:10 2023

@author: marcelvnguemaha
https://stackoverflow.com/questions/63592900/plotly-dash-how-to-design-the-layout-using-dash-bootstrap-components
https://dash-bootstrap-components.opensource.faculty.ai/docs/components/layout/

"""
from dash.dependencies import Input, Output
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import gunicorn #whilst your local machine's webserver doesn't need this, Heroku's linux webserver (i.e. dyno) does. I.e. This is your HTTP server
from whitenoise import WhiteNoise   #for serving static files on Heroku
import pandas as pd
import helpers

from urllib.request import urlopen
import json
with urlopen(
        'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    geojson_counties = json.load(response)


#get the data from public repos
df = pd.read_parquet('https://github.com/nmmarcelnv/cmsdatajam/blob/main/data/DataProcessed.parquet?raw=true')
ckd_inc_df = pd.read_excel(
    'https://github.com/nmmarcelnv/cmsdatajam/blob/main/reports/charts.xlsx?raw=true',
    sheet_name='CKD Incidence Research',
    usecols=['DASH Score', 'Odds ratio']
).dropna()
diet_df = pd.read_excel(
    'https://github.com/nmmarcelnv/cmsdatajam/blob/main/reports/charts.xlsx?raw=true',
    sheet_name='Diet Followed'
).sort_values(by=['Percentage of population'])
#ckd_inc_df['Odds ratio'] = ckd_inc_df['Odds ratio'] * 100
ckd_inc_df = ckd_inc_df[ckd_inc_df['DASH Score']!=1]
diet_df['Percentage of population'] = diet_df['Percentage of population'] * 100
cmin, cmax = 20, 40
fips_options = df['FIPS']
metrics_options=[
    'unEmpRate','PovertyRate',
    'laseniors1','laseniors10','laseniors20',
    'lalowi1',	'lalowi10',	'lalowi20',
    'lasnap1','lasnap10','lasnap20',
    'TractWhite','TractBlack','TractAsian','TractNHOPI','TractAIAN','TractOMultir','TractSNAP'
    
]


def get_correlation(df, year=2019):
    
    import scipy
    def assign_distance(x):
    
        if '20' in x[-2:]: return '20 Miles'
        if '10' in x[-2:]: return '10 Miles'
        if ('1' in x[-2:])&(any(c.isalpha() for c in x[-2:])): return '1 Miles'
        if 'lf' in x[-2:]: return '0.5 Miles'
        return x

    def assign_names(x):

        if 'lalow' in x: return 'Low Income Pop'
        if 'laseniors' in x: return 'Senior Pop'
        if 'lasnap' in x: return 'SNAP Pop'
        return x

    
    dff = df[(df.Year==2019)]
    cols = [
        'CkdRate','unEmpRate', 'PovertyRate', 
        'lalowihalf','lalowi1','lalowi10', 'lalowi20', 
        'laseniorshalf','laseniors1', 'laseniors10', 'laseniors20',
        'lasnaphalf', 'lasnap1', 'lasnap10','lasnap20', 
        'TractWhite', 'TractBlack',
        'TractAsian', 'TractNHOPI', 'TractAIAN', 'TractOMultir', 'TractSNAP']
    
    dd = pd.DataFrame()
    feats = []
    corrs = []
    p_values = []
    feat='CkdRate'
    for feati in cols:
        #if feati != feat:
            feats.append(feati)
            corr, p_value = scipy.stats.spearmanr(dff[feat], dff[feati])
            corrs.append(corr)
            p_values.append(p_value)

    dd['Feature'] = feats
    dd['Correlation Coeff with CKD'] = corrs
    dd['p_value'] = [round(x, 4) for x in p_values]
    
    dd['Distance from supermarket'] = dd['Feature'].apply(assign_distance)
    dd['Population Group'] = dd['Feature'].apply(assign_names)
    dd = dd.sort_values(
        by=['Population Group','Distance from supermarket'])
    dd = dd[['Population Group','Distance from supermarket','Correlation Coeff with CKD', 'p_value']]

    cols1 = ['CkdRate','unEmpRate','PovertyRate','TractWhite', 'TractBlack',
       'TractAsian', 'TractNHOPI', 'TractAIAN', 'TractOMultir', 'TractSNAP']
    
    d1 = dd[~dd['Population Group'].isin(cols1)]
    d2 = dd[dd['Population Group'].isin(cols1)]
    d2 = d2.rename(columns={'Distance from supermarket':'Social Determinant'})
    d2['Social Determinant']=d2['Social Determinant'].apply(lambda x: x.replace('Tract', 'Proportion of '))

    return d1, d2
    

corr_df1, corr_df2 = get_correlation(df, year=2019)

def drawMap(object_id, metric='CkdRate', xrange=(20, 40)):
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.choropleth(
                        df[df.Year==2019], 
                        geojson=geojson_counties,
                        locations="FIPS", 
                        color=metric,
                        scope='usa',
                        color_continuous_scale='YlOrRd',
                        range_color=xrange,
                        hover_data = {'State':True, 'County':True},
                        labels={'CkdRate':'CKD Prevalence (%)'},
                        
                    ),
                ) 
            ])
        ),  
    ])

def drawCKDIncidence(object_id):
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.scatter(
                        ckd_inc_df, x="DASH Score", y="Odds ratio",size='Odds ratio',
                        title='CKD Incidence by DASH adherence score (Goolaleh et al. 2017 research)'
                    ),
                ) 
            ])
        ),  
    ])


def drawDiet(object_id):
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.bar(
                        diet_df, x="Percentage of population", y="Type of Diet", 
                        title='Type of diet by % of US population',
                        #color=['blue' if x!='DASH diet' else 'red' for x in diet_df['Type of Diet']]
                        orientation='h'
                    ),
                ) 
            ])
        ),  
    ])

def drawBar(object_id):
    data = df.groupby(['Year'])[['CkdRate']].mean().reset_index()
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.bar(data, x="Year", y="CkdRate"),
                ) 
            ])
        ),  
    ])

def drawCorr1(object_id):
    
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.bar(
                        corr_df1, 
                        x="Distance from supermarket", 
                        y="Correlation Coeff with CKD",
                        color='Population Group', 
                        barmode='group',
                        hover_data = {'p_value':True, },
                        title='Correlation between CKD prevalence and access to healthy food'
                    )
                ) 
            ])
        ),  
    ])

def drawCorr2(object_id):
    
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.bar(
                        corr_df2, 
                        x="Social Determinant", 
                        y="Correlation Coeff with CKD",
                        color=['blue' if x>0 else 'red' for x in corr_df2['Correlation Coeff with CKD']],
                        barmode='group',
                        hover_data = {'p_value':True, },
                        title='Correlation between CKD prevalence and various social determinants'
                    ).update(layout_showlegend=False)
                    
                ) 
            ])
        ),  
    ])


# Text field
def drawText():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H2("Text"),
                ], style={'textAlign': 'center'}) 
            ])
        ),
    ])


def getIntro():
    return html.Div(
        className="header",
        children=[
            html.H1("2023 Health Equity Datajam: A Practical Guide Reduce Chronic Kidney Disease (CKD)"),
            html.H5([
                "Contributors: ",
                html.Span("Marcel Nguemaha", style={"color": "white", "font-weight": "bold"}),
                " and ",
                html.Span("Priyanka Garde", style={"color": "white", "font-weight": "bold"}),
                " (National Government Services)"
            ]),
            html.Hr(),
            html.P(
        "According to Center of Disease Control (CDC) reports, more than 15% of US adults \
            are estimated to have CKD and 9 in 10 adults with CKD are unaware of their condition. \
                Also, African American and other minority population, mostly living in under-served c\
                    ommunities are more that 4 times as likely as Whites to develop Kidney Failure."
            ),
            
        ]
    )



def section_correlation():
    
    return html.Div(
        className="header",
        children=[
            html.Hr(),
            html.H1([
                html.Span(
                    "Correlation Between CKD Prevalence and various social determinants", 
                    style={"color": "green", "font-weight": "bold"}
                ),
            ]),
            html.H5([
                html.Span("NOTE: ", style={"color": "white", "font-weight": "bold"}),
                " Correlation does not imply causation",
            ]),
            html.Hr(),
        
            html.Label([
                "We've computed the Spearman correlation to assess the relationship between variables. ",
                 html.A('The Spearman correlation ', href='https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient'), 
                 "is a statistical tool used to measure the strength and direction of the relationship \
                     between two variables. The larger the absolute value, the stronger the relationship between the variables.\
                     A positive value close to +1 indicates that one variable may likely increase if we increase the other, while \
                     a negative value close to -1 means one variable might decrease if we increase the other. \
                     For example, the data shows a positive correlation between CKD prevalence and poverty rate. \
                    This means that areas with higher poverty rates are also more likely to have a higher prevalence of CKD. \
                    Spearman's correlation can help us better understand the relationship between CKD prevalence and\
                        other social determinants of health ", 
            ])
            
        ]
    )
     

def section_food_survey():
    
    return html.Div(
        className="header",
        children=[
            html.Hr(),
            html.H1([
                html.Span(
                    "Using Research Studies on Food and Health to Inform Decisions", 
                    style={"color": "green", "font-weight": "bold"}
                ),
            ]),
            html.H5([
                html.Span(
                    "Food Insecurity, Food Deserts and Food Swamps are not good for Kidney Health ", 
                    style={"color": "white", "font-weight": "bold"}
                ),
            ]),
            html.Hr(),
        
            html.Label([
                "It is known that healthy diet can reduce the risk of conditions such as diabetes and hypertension, \
                which are the primary risk factors for CKD. In particular, there is ",
                html.A('The data ', href='https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6602537/'), 
                "shows that adherence to the ", 
                html.A('Dietary Approach to Stop Hypertension (DASH)', 
                       href='https://www.hsph.harvard.edu/nutritionsource/healthy-weight/diet-reviews/dash-diet/'), 
                " reduced the risk of CKD by up to 10%. The problem however is that adherence to healthy eating habits \
                such as the DASH diet is particularly low among black and other minority groups, \
                which unfortunately have the highest prevalence of CKD in the US."
            ])
            
        ]
    )


# Build App
app = Dash(__name__, external_stylesheets=[dbc.themes.SLATE])

server = app.server 
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

app.layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            #Header row
            dbc.Row([
                dbc.Col([
                    getIntro(),
                ], width=12),
                
            ], align='center'), 
            
            #A row
            html.Br(),
            dbc.Row([
                dbc.Col([
                    
                    html.Label('Select CKD Prevalence Range:'),
                    dcc.RangeSlider(
                        id='c-range-slider',
                        min=0,
                        max=100,
                        step=1,
                        value=[cmin, cmax],
                        marks={x: str(x) for x in [0,20,40,60,80,100]}
                    ),
                    
                ], width=2),
                dbc.Col([
                    
                    html.Label('Select Year:'),
                    dcc.RadioItems(
                        id='year-picker',
                        options=[2005,2010,2015,2019,2024], 
                        value=2019, 
                        inline=True
                    ),
                    
                ], width=2),
                dbc.Col([
                    
                    dbc.Button(
                        'Click to Make Predictions', id='btn-nclicks', n_clicks=0,color="success",),
                    
                ], width=2),
                
                #######
                dbc.Col([
                    
                    html.Label('Select Percentage Range:'),
                    dcc.RangeSlider(
                        id='metric-range-slider',
                        min=0,
                        max=100,
                        step=1,
                        value=[cmin, cmax],
                        marks={x: str(x) for x in [0,20,40,60,80,100]}
                    ),
                    
                ], width=2),
                
                ######
                dbc.Col([
                    html.Label('Select FIPS'),
                    dcc.Input(
                        id="fips-id", 
                        type="text", 
                        placeholder="00000", 
                        value='00000',
                        #style={'marginRight':'10px'}
                    ),
                        
                ], width=2),
                
                dbc.Col([
                    html.Label('Select Metric'),
                    
                    dcc.Dropdown(
                        options=metrics_options, 
                        value='unEmpRate', 
                        id='metric-dropdown'
                    ),
                        
                ], width=2),
                
            ], align='center'), 
            
            #Another row
            html.Br(),
            dbc.Row([
                dbc.Col([
                    drawMap(object_id='ckd-map-id')
                ], width=6),
                
                dbc.Col([
                    drawMap(object_id='metrics-map-id', metric='unEmpRate') 
                ], width=6),
            ], align='center'), 
            
            #Another row
            html.Br(),
            dbc.Row([
                dbc.Col([
                    drawBar(object_id='ckd-scatter-id')
                ], width=9),
                
                dbc.Col([
                    html.Label('Adjust % Senior'),
                    dcc.Input(
                        id="perc-senior", type="number", placeholder="Adjust % Senior",
                        min=0, max=1, step=0.1, value=0
                    ),
                ], width=1),
                dbc.Col([
                    html.Label('Adjust % Low Income'),
                    dcc.Input(
                        id="perc-lowi", type="number", placeholder="Adjust % Low Income",
                        min=0, max=1, step=0.1, value=0
                    ),
                ], width=1),
                dbc.Col([
                    html.Label('Adjust % SNAP'),
                    dcc.Input(
                        id="perc-snap", type="number", placeholder="Adjust % SNAP",
                        min=0, max=10, step=1, value=0
                    ),
                ], width=1),
                
            ], align='center'),   
            
            #Another row
            dbc.Row([
                dbc.Col([
                    section_food_survey(),
                ], width=12),
                
            ], align='center'), 
            html.Br(),
            dbc.Row([
                dbc.Col([
                    drawCKDIncidence(object_id='ckd-inc-id')
                ], width=6),
                dbc.Col([
                    drawDiet(object_id='diet-id') 
                ], width=6),
            ], align='center'),  
            
            #Another row
            dbc.Row([
                dbc.Col([
                    section_correlation(),
                ], width=12),
                
            ], align='center'), 
            html.Br(),
            dbc.Row([
                dbc.Col([
                    drawCorr1(object_id='corr1-id') 
                ], width=6),
                
                dbc.Col([
                    drawCorr2(object_id='corr2-id') 
                ], width=6),
            ], align='center'),
            
        ]), color = 'dark'
    )
])



# Create a callback to update the range_color of the choropleth map based on the slider value
@app.callback(
    Output('ckd-map-id', 'figure'),
    [
     Input('c-range-slider', 'value'),
     Input('year-picker', 'value'),
     Input('btn-nclicks', 'n_clicks'),
     Input('perc-senior', 'value'),
     Input('perc-lowi', 'value'),
     Input('perc-snap', 'value'),
    ]
)
def update_map(ckdvalues,year,btn,perc_senior,perc_lowi,perc_snap):
    cmin = ckdvalues[0]
    cmax = ckdvalues[1]
    
    data = df[df.Year==year].copy()
    if (year==2024)&(btn==0):
        year=19999999
        data = df[df.Year==year].copy()
    elif (year==2024)&(btn>0):
        
        test_df = df[(df.Year>2015)].copy()
        data = helpers.make_predictions(test_df,perc_senior,perc_lowi,perc_snap)
       
    
    fig = px.choropleth(
        data, 
        geojson=geojson_counties,
        locations="FIPS", 
        color='CkdRate',
        scope='usa',
        color_continuous_scale='YlOrRd',
        range_color=(cmin, cmax),
        hover_data = {'State':True, 'County':True},
        labels={'CkdRate':'CKD Prevalence (%)'},
        title='CKD Prevalence by US Counties',
    )
    
    return fig


@app.callback(
    Output('ckd-scatter-id', 'figure'),
    [
     Input('year-picker', 'value'),
     Input('btn-nclicks', 'n_clicks'),
     Input('perc-senior', 'value'),
     Input('perc-lowi', 'value'),
     Input('perc-snap', 'value'),
    ]
)
def update_scatter(year,btn,perc_senior,perc_lowi,perc_snap):
    
    data = df[df.Year==year].copy()
    if (year==2024)&(btn==0):
        year=19999999
        data = df[df.Year==year].copy()
    elif (year==2024)&(btn>0):
        
        test_df = df[(df.Year>2015)].copy()
        test_df['Year'] = year
        data = helpers.make_predictions(test_df,perc_senior,perc_lowi,perc_snap)
       

    data = pd.concat([df, data])
    actual = data.groupby(['Year'])[['CkdRate']].mean().reset_index()
    
    actual['Data Label'] = 'Actual'
    pred = actual.copy()
    
    for year in [2017,2018,2019]:
        pred.loc[pred.Year==year,'CkdRate'] =\
            1.05*pred.loc[pred.Year.isin([year-2,year-1]),'CkdRate'].mean()
    pred.loc[pred.Year==2024,'CkdRate'] = \
        1.05*pred.loc[pred.Year.isin([2018,2019,2024]),'CkdRate'].mean()
    pred['Data Label'] = 'Predicted'
    actual_df = actual[actual.Year<2024]
    pred_df = pred[pred.Year>=2017]
    
    if btn==0:
        dff = actual_df
    else:
        dff = pd.concat([actual_df,pred_df])
    
    dff['CkdRate']=dff['CkdRate'].apply(lambda x:round(x,1))
    dff = dff.rename(columns={'CkdRate':'Avg CKD Rate (%)'})
    
    fig = px.scatter(
        dff, x='Year', 
        y='Avg CKD Rate (%)', 
        color='Data Label', 
        size='Avg CKD Rate (%)',
        text='Avg CKD Rate (%)',
        title='CKD prevalence in the US has been increase over the years'
    )
    fig.update(layout_showlegend=False)
    fig.update_traces(textposition="top center")
    return fig



@app.callback(
    Output('metrics-map-id', 'figure'),
    [
     Input('metric-dropdown', 'value'),
     Input('perc-senior', 'value'),
     Input('perc-lowi', 'value'),
     Input('perc-snap', 'value'),
     Input('fips-id', 'value'),
     Input('metric-range-slider','value'),
    ]
)
def update_metric_map(metric,perc_senior,perc_lowi,perc_snap,fips_id,metric_range):
    cmin, cmax = metric_range[0], metric_range[1]
    #data = df[df.Year==2019].copy()
    if fips_id!='00000':
        data = df[(df.Year==2019)&(df.FIPS==fips_id)].copy()
    else:
        data = df[df.Year==2019].copy()
    data['laseniors10'] = data['laseniors10']*perc_senior
    data['lalowi10'] = data['lalowi10']*perc_lowi
    data['lasnap10'] = data['lasnap10']*perc_snap
    fig = px.choropleth(
        data, 
        geojson=geojson_counties,
        locations="FIPS", 
        color=metric,
        scope='usa',
        color_continuous_scale='YlOrRd',
        range_color=(cmin, cmax),
        hover_data = {'State':True, 'County':True},
        labels={'CkdRate':'CKD Prevalence (%)'},
    )
    
    return fig


# Run flask app
if __name__ == "__main__": 
    app.run_server(debug=False, host='0.0.0.0', port=8050)