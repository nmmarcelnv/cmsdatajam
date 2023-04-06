import plotly.express as px
import pandas as pd
import dash
from dash.dependencies import Input, Output
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import gunicorn 
from whitenoise import WhiteNoise   

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

# Instantiate dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Reference the underlying flask app (Used by gunicorn webserver in Heroku production deployment)
server = app.server 

# Enable Whitenoise for serving static files from Heroku (the /static folder is seen as root by Heroku) 
server.wsgi_app = WhiteNoise(server.wsgi_app, root='static/') 

app.layout = html.Div([
    dcc.Graph(id='ckd-map', figure=fig)
])


# Run flask app
if __name__ == "__main__": 
    app.run_server(debug=False, host='0.0.0.0', port=8050)
