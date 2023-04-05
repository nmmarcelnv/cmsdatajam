import plotly.figure_factory as ff
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


ckd.columns=['ckd_value','county','state']
ckd['county'] = ckd['county'].str.upper()
ckd['state'] = ckd['state'].str.upper()
ckd = ckd[['state','county','ckd_value']]

df = pd.merge(ckd, fips,on=['state','county'])

colorscale = ["#f7fbff","#ebf3fb","#deebf7","#d2e3f3","#c6dbef","#b3d2e9","#9ecae1",
              "#85bcdb","#6baed6","#57a0ce","#4292c6","#3082be","#2171b5","#1361a9",
              "#08519c","#0b4083","#08306b"]
colorscale = ["#f7fbff", "#d4e9f7", "#afd6ef", "#8fbfe8", "#7197c5", "#58719f", "#3d4f7f", "#2a2a5a", "#151531"]
colorscale = [
    'rgb(193, 193, 193)',
    'rgb(239,239,239)',
    'rgb(195, 196, 222)',
    'rgb(144,148,194)',
    'rgb(101,104,168)',
    'rgb(65, 53, 132)',
    'rgb(63.0, 188.0, 115.0)',
]
endpts = list(np.linspace(1, 100, len(colorscale) - 1))
endpts = [0, 10, 20, 30, 40, 100]
fips_values = df['fips'].tolist()
ckd_values = df['ckd_value'].tolist()

# Instantiate dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server 

# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku) 
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

app.layout = html.Div([
    dcc.Dropdown(
        id='state-dropdown',
        options=[{'label': state, 'value': state} for state in df['state'].unique()],
        value='Alabama'
    ),
    dcc.Graph(id='ckd-map')
])


@app.callback(
    Output('ckd-map', 'figure'),
    Input('state-dropdown', 'value')
)
def update_map(selected_state):
    filtered_df = df[df['state'] == selected_state]
    fips_values = filtered_df['fips'].tolist()
    ckd_values = filtered_df['ckd_value'].tolist()
    fig = ff.create_choropleth(
        fips=fips_values, values=ckd_values,
        binning_endpoints=endpts,
        colorscale=colorscale,
        scope=[selected_state],
        show_state_data=True,
        show_hover=True, centroid_marker={'opacity': 0},
        asp=2.9, title='CKD Prevalence',
        legend_title='% CKD'
    )
    return fig

# Run flask app
if __name__ == "__main__": 
    app.run_server(debug=False, host='0.0.0.0', port=8050)
