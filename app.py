import plotly.express as px
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output
from dash import Dash, callback, html, dcc
import dash_bootstrap_components as dbc
import gunicorn #whilst your local machine's webserver doesn't need this, Heroku's linux webserver (i.e. dyno) does. I.e. This is your HTTP server
from whitenoise import WhiteNoise   #for serving static files on Heroku



dtypes = {
    'StateFIPS':str,
    'CountyFIPS_3':str,
    'CountyName':str,
    'StateName':str,
    'CountyFIPS':str,
    'StateAbbr':str,
    'STATE_COUNTY':str
}

ckd = pd.read_csv('https://raw.githubusercontent.com/nmmarcelnv/cmsdatajam/main/data/Prevalence_of_CKD_by_US_State_and_County_by_County_2019.csv')
fips = pd.read_csv(
    'https://raw.githubusercontent.com/ChuckConnell/articles/master/fips2county.tsv',
    sep='\t',
    usecols=['CountyName','StateName','CountyFIPS','StateAbbr'],
    dtype=dtypes
)

fips.columns=['county','state','fips', 'state3']
fips = fips[['state','county','fips', 'state3']]
fips['county'] = fips['county'].str.upper()
fips['state'] = fips['state'].str.upper()


ckd.columns=['cases','county','state']
ckd['county'] = ckd['county'].str.upper()
ckd['state'] = ckd['state'].str.upper()
ckd = ckd[['state','county','cases']]

df = pd.merge(ckd, fips,on=['state','county'])

#df = pd.read_parquet('../data.parquet')
# Instantiate dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

server = app.server 

server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

cmin, cmax = 20, 40

fig = px.choropleth(
    df, 
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations="fips", 
    color='cases',
    scope='usa',
    color_continuous_scale='YlOrRd',
    range_color=(cmin, cmax),
    hover_data = {'state':True, 'county':True},
    labels={'cases':'CKD Prevalence (%)'}
)

# Create layout with input components and the choropleth map
app.layout = html.Div([
    dbc.Row([
        dbc.Col(
            dcc.Input(
                id='cmin-input',
                type='number',
                value=cmin,
                min=0,
                max=100,
                step=1,
                placeholder='Enter a min value'
            ), 
            width={'size': 2, 'offset': 1}
        ),
        dbc.Col(
            dcc.Input(
                id='cmax-input',
                type='number',
                value=cmax,
                min=0,
                max=100,
                step=1,
                placeholder='Enter a max value'
            ), 
            width={'size': 2, 'offset': 1}
        ),
    ], align='center', justify='center', className='mt-3 mb-3'),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='ckd-map', figure=fig),
            width={'size': 10, 'offset': 1}
        )
    ])
])

# Create a callback to update the range_color of the choropleth map based on the input values
@app.callback(
    Output('ckd-map', 'figure'),
    Input('cmin-input', 'value'),
    Input('cmax-input', 'value')
)
def update_map(cmin, cmax):
    fig = px.choropleth(
        df, 
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
        locations="fips", 
        color='cases',
        scope='usa',
        color_continuous_scale='YlOrRd',
        range_color=(cmin, cmax),
        hover_data = {'state':True, 'county':True},
        labels={'cases':'CKD Prevalence (%)'}
    )
    return fig

# Run flask app
if __name__ == "__main__": 
    app.run_server(debug=False, host='0.0.0.0', port=8050)