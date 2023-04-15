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


cmin, cmax = 20, 40
dropdown_options=[
    'unEmpRate','laseniors1','laseniors10','laseniors20','lalowi1',	'lalowi10',	'lalowi20',	'lasnap1','lasnap10','lasnap20']
# Iris bar figure
def drawMap(object_id, metric='CkdRate', xrange=(20, 40)):
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.choropleth(
                        df[df.Year==2019], 
                        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
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

#get the data from public repos
df = pd.read_parquet('https://github.com/nmmarcelnv/cmsdatajam/blob/main/data/DataProcessed.parquet?raw=true')

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
                
                dbc.Col([
                    html.Label('Select Metric'),
                    
                    dcc.Dropdown(
                        options=dropdown_options, 
                        value='unEmpRate', 
                        id='metric-dropdown'
                    ),
                        
                ], width=3),
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
                    drawBar(object_id='ckd-bar-id')
                ], width=6),
                dbc.Col([
                    drawMap(object_id='ckd-map-id3', metric='lalowi20')
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
    ]
)
def update_map(ckdvalues,year,btn):
    cmin = ckdvalues[0]
    cmax = ckdvalues[1]
    
    data = df[df.Year==year].copy()
    if (year==2024)&(btn==0):
        year=19999999
        data = df[df.Year==year].copy()
    elif (year==2024)&(btn>0):
        
        test_df = df[(df.Year>2015)].copy()
        data = helpers.make_predictions(test_df,year)
       

    fig = px.choropleth(
        data, 
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
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
    Output('metrics-map-id', 'figure'),
    [
     Input('metric-dropdown', 'value'),
    ]
)
def update_metric_map(metric):
    
    data = df[df.Year==2019].copy()

    fig = px.choropleth(
        data, 
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
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