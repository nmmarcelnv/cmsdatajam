#import plotly.figure_factory as ff
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



# Instantiate dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server 

# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku) 
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 


fig = px.choropleth(
    df, 
    geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
    locations="fips", 
    color="cases",
    scope="usa",
    color_continuous_scale="Viridis",
    range_color=[0,50],
    labels={'cases':'CKD Prevalence (%)'}
)

app.layout = html.Div([
    dcc.Graph(id='ckd-map', figure=fig)
])


"""
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
    filtered_df['fips'] = filtered_df['fips'].astype(str).str.zfill(5)
    fig = ff.create_choropleth(
        fips=filtered_df['fips'].tolist(), 
        values=filtered_df['cases'].tolist(),
        binning_endpoints=endpts,
        colorscale=colorscale,
        scope=['USA'],
        show_state_data=True,
        show_hover=True, centroid_marker={'opacity': 0},
        asp=2.9, title='CKD Prevalence',
        legend_title='% CKD'
    )
    fig.layout.template = None
"""    

# Run flask app
if __name__ == "__main__": 
    app.run_server(debug=False, host='0.0.0.0', port=8050)
