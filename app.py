import plotly.express as px
import pandas as pd
import datetime as dt
import numpy as np
import dash
from dash.dependencies import Input, Output
from dash import Dash, callback, html, dcc
import dash_bootstrap_components as dbc
import gunicorn #whilst your local machine's webserver doesn't need this, Heroku's linux webserver (i.e. dyno) does. I.e. This is your HTTP server
from whitenoise import WhiteNoise   #for serving static files on Heroku

#get the data from public repos
df = pd.read_parquet('https://github.com/nmmarcelnv/cmsdatajam/blob/main/data/DataProcessed.parquet?raw=true')

# Define options for the year dropdown
year_options = [{'label': year, 'value': year} for year in sorted(df['Year'].unique())]

# Instantiate dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

server = app.server 

server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

cmin, cmax = 20, 40
# Create initial figures
fig = px.choropleth(
    df[df.Year==2019], 
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations="FIPS", 
    color='CkdRate',
    scope='usa',
    color_continuous_scale='YlOrRd',
    range_color=(cmin, cmax),
    hover_data = {'State':True, 'County':True},
    labels={'CkdRate':'CKD Prevalence (%)'},
    title='CKD Prevalence by US Counties (2019)',
)

fig2 = px.choropleth(
    df, 
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations="FIPS", 
    color='unEmpRate',
    scope='usa',
    color_continuous_scale='YlOrRd',
    range_color=(cmin, cmax),
    hover_data = {'State':True, 'County':True},
    labels={'PovertyRate':'Poverty Rate'},
    title='Poverty Rate by US Counties',
)


# Create layout with input components and the choropleth map
# Set the layout of the app
app.layout = html.Div(
    style={'backgroundColor': '#f2f2f2', 'border': '5px solid #555'},
    children=[
        # Header section
        html.Div(
            className="header",
            children=[
                html.H1("2023 Health Equity Datajam: A Practical Guide Reduce Chronic Kidney Disease (CKD)"),
                html.H5([
                    "Contributors: ",
                    html.Span("Marcel Nguemaha", style={"color": "blue", "font-weight": "bold"}),
                    " and ",
                    html.Span("Priyanka Garde", style={"color": "blue", "font-weight": "bold"}),
                    " (National Government Services)"
                ]),
                html.Hr(),
                html.P(
            "According to Center of Disease Control (CDC) reports, more than 15% of US adults are estimated to have CKD and 9 in 10 adults with CKD are unaware of their condition. Also, African American and other minority population, mostly living in under-served communities are more that 4 times as likely as Whites to develop Kidney Failure."
                ),
            ]
        ),

        # Main content section
        html.Div(
            className="main-content",
            children=[
                # Input panel section
                html.Div(
                    className="input-panel",
                    children=[
                        
                        html.Label('Select Year:'),
                        dcc.RadioItems(
                            id='year-picker',
                            options=[  2005,2010,2015,2019,2023], 
                            value=2019, 
                            inline=True
                        ),
                        html.Label('Select CKD Prevalence Range:'),
                        dcc.RangeSlider(
                            id='c-range-slider',
                            min=0,
                            max=100,
                            step=1,
                            value=[cmin, cmax],
                            marks={x: str(x) for x in [0,20,40,60,80,10]}
                        ),
                    ],
                    style={'width': '48%', 'display': 'inline-block'}
                ),

                # Map section
                html.Div(
                    className="map-section",
                    children=[
                        dcc.Graph(
                            id='ckd-map',
                            figure=fig,
                            style={'width': '48%', 'display': 'inline-block'}
                        ),
                        dcc.Graph(
                            id='poverty-map',
                            figure=fig2,
                            style={'width': '48%', 'display': 'inline-block', 'float': 'right'}
                        )
                    ]
                ),
            ]
        ),
    ],
    className="container"
)


# Create a callback to update the range_color of the choropleth map based on the slider value
@app.callback(
    Output('ckd-map', 'figure'),
    [Input('year-picker', 'value'),
     Input('c-range-slider', 'value')]
)
def update_map(year,ckdvalues):
    cmin = ckdvalues[0]
    cmax = ckdvalues[1]
    
    fig = px.choropleth(
        df[df.Year==year], 
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

# Run flask app
if __name__ == "__main__": 
    app.run_server(debug=False, host='0.0.0.0', port=8050)