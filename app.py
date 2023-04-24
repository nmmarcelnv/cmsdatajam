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

#source: https://www.fns.usda.gov/snap/foods-typically-purchased-supplemental-nutrition-assistance-program-snap-households
usecols=['Food Category','Percentage of Total Spend']
foods = pd.read_excel(
    'https://github.com/nmmarcelnv/cmsdatajam/blob/main/reports/charts.xlsx?raw=true',
    sheet_name='What SNAP People Buy', usecols=usecols)
foods = foods[foods['Food Category']!='Total Summary Category Expenditures']
foods['Percentage of Total Spend'] = foods['Percentage of Total Spend'] * 100

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

        if 'lalow' in x: return 'Low Income'
        if 'laseniors' in x: return 'Senior'
        if 'lasnap' in x: return 'SNAP'
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
                        #width=800, height=400,
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

def drawSNAPSpends(object_id):
    
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    id=object_id,
                    figure = px.bar(
                        foods, 
                        x="Food Category", 
                        y="Percentage of Total Spend",
                        barmode='group',
                        title='Percentage of Total Expenditures by Food Category for SNAP households'
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
            html.H1("Healthy Food for Healthy Kidney: A strategy customized to the unique needs of each community"),
            html.H5([
                html.Span(" Marcel Nguemaha", style={"color": "white", "font-weight": "bold",}),
                " and ",
                html.Span("Priyanka Garde", style={"color": "white", "font-weight": "bold"}),
                " (National Government Services)"
            ]),
            
            
        ]
    )
     

def section_food_survey():
    
    return html.Div(
        className="header",
        children=[
            html.Hr(),
            html.H1([
                html.Span(
                    "Breaking down barriers to healthy eating: Addressing Disparities in CKD through targeted nutrition strategies", 
                    style={"color": "green", "font-weight": "bold"}
                ),
            ]),
            html.H5([
                html.Span(
                    "Food Insecurity, Food Deserts and Food Swamps are not good for Kidney Health\
                    a community customized DASH program can help but adherence is low among high-risk populations", 
                    style={"color": "white", "font-weight": "bold"}
                ),
            ]),
            html.Hr(),
        
            html.Label([
                "It is known that healthy diet can reduce the risk of conditions such as diabetes and hypertension, \
                which are the primary risk factors for CKD. In particular, ",
                html.A('the data ', href='https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6602537/'), 
                "shows that adherence to the ", 
                html.A('Dietary Approach to Stop Hypertension (DASH)', 
                       href='https://www.hsph.harvard.edu/nutritionsource/healthy-weight/diet-reviews/dash-diet/'), 
                " can reduce the risk of CKD by up to 10%. The problem however is that adherence to healthy eating habits \
                such as the DASH diet is particularly low among black and other minority groups, \
                which unfortunately have the highest prevalence of CKD in the US. This means that the traditional \
                one-fit-all DASH approach is not designed to address the unique challenges that specific communities face.\
                Indeed, sample responses from black individuals with stage 3-4 CKD ellucidate this point: " ,
                html.A('(Tyson et al. Journal of Renal Nutrition, Vol 33, Issue 1, p59-68, 2023)', 
                       href='https://www.sciencedirect.com/science/article/pii/S1051227622000887'), 
                html.Br(),
                html.Span(
                    "Yeah because the stores that I shop, they have all of this but I would still say the expense. \
                    I’m on disability so I make a certain amount of money and after paying the car note and some \
                    other stuff and then for my food stamps I only get like $19 a month so that doesn’t go very far." , 
                    style={"color": "yellow", 'font-style': 'italic', 'text-align': 'center', 'margin': '0 auto', 'display': 'block', 'width': '80%'}
                ),
                
                html.Br(),
                html.Span(
                    "The way the instructions are they don’t make it as simple for people that doesn’t have experience in cooking." , 
                    style={"color": "yellow", 'font-style': 'italic', 'text-align': 'center', 'margin': '0 auto', 'display': 'block', 'width': '80%'}
                ),
                
            ])
            
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
            html.H5([
                html.Span("Highlight: ", style={"color": "white", "font-weight": "bold"}),
                " Though SNAP benefits might help with hunger, food items commonly purchased\
                with SNAP benefits are not particularly helpful for Kidney Health",
            ]),
            html.Hr(),
        
            html.Label([
                "We've computed the Spearman correlation to assess the relationship between the prevalence of CKD and other social determinants of health. ",
                 html.A('The Spearman correlation ', href='https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient'), 
                 "is a statistical tool used to measure the strength and direction of the relationship \
                     between two variables. The larger the absolute value, the stronger the relationship between the variables.\
                     A positive value close to +1 indicates that one variable may likely increase if we increase the other, while \
                     a negative value close to -1 means one variable might decrease if we increase the other. \
                     For example, the data shows a positive correlation between CKD prevalence and poverty rate. \
                    This means that areas with higher poverty rates are also more likely to have a higher prevalence of CKD. \
                    Interestingly, we found that for populations living closer to a supermarket, receiving SNAP benefit has a \
                    positive correlation with the prevalence of CKD whereas for those living further away from a supermarket, \
                    receiving SNAP benefit correlates negatively with CKD. This suggests that people living closer to a supermarket \
                    may be using their SNAP benefits to purchase items that aggravage the risk of developing CKD. "
            ])
            
        ]
    )
        

def section_resources():
    
    return html.Div(
        className="header",
        children=[
            html.Hr(),
            html.H1([
                html.Span(
                    "US Kidney Health Atlas: A one-stop shop for various Kidney Health resources", 
                    style={"color": "green", "font-weight": "bold"}
                ),
            ]),
            
            html.H5([
                html.Span(
                    "Patients, caregiver, providers, and researchers have a hard time navigating through the \
                    vast amount of information scattered all over the internet.", 
                    style={"color": "white", "font-weight": "bold"}
                ),
            ]),
            html.Hr(),
        
            html.Label([
                "",
                 html.A(
                     'The Center of Disease Control and Prevention (CDC) Chronic Kidney Disease Initiative :', 
                     href='https://www.cdc.gov/kidneydisease/publications-resources/ckd-national-facts.html',
                     target='_blank'), 
                 "", " Go here for general information about CKD statistics in the US as well as basics health tips"
            ]),
            
            html.Label([
                "",
                 html.A(
                     'Organ Donation and Transplantation :', 
                     href='https://data.hrsa.gov/topics/health-systems/organ-donation',
                     target='_blank'), 
                 "", " Information about Organ donation and transplant for various Organs, including Kidney. You can see approximate\
                     wait time by gender, race, age etc ... "
            ]),
                
            html.Label([
                "",
                 html.A(
                     'Dialysis Units in the USA :', 
                     href='hhttps://www.dialysisunits.com',
                     target='_blank'), 
                 "", " This is a great tool for CKD patients. You can find dialysis unit in your regions, including home dialysis centers "
            ]),
                
            html.Label([
                "",
                 html.A(
                     'The National Institute of Diabetes and Digestive and Kidney Diseases :', 
                     href='https://www.niddk.nih.gov/about-niddk/strategic-plans-reports/usrds/data-query-tools/esrd-incident-count',
                     target='_blank'), 
                 "", " This tool can be used to display counts of incident ESRD patients. \
                     The specific population of interest and the display format can be configured by the user. \
                         Specific instructions for use are also provided. This is great for data analysis and modeling"
            ]),
                
            html.Label([
                "",
                 html.A(
                     'Mapping Medicare Disparities by Population :', 
                     href='https://data.cms.gov/tools/mapping-medicare-disparities-by-population',
                     target='_blank'), 
                 "", " provides a user friendly way to explore and better understand disparities in chronic diseases."
            ]),
            
            html.Label([
                "",
                 html.A(
                     'CDC Social Determinants of Health :', 
                     href='https://gis.cdc.gov/grasp/diabetes/diabetesatlas-sdoh.html',
                     target='_blank'), 
                 "", " Diabetes Atlas, shows percentage of diagnosed diabetes by US state."
            ]),
            
            html.Label([
                "",
                 html.A(
                     'Food Access Atlas :', 
                     href='https://www.ers.usda.gov/data-products/food-access-research-atlas/download-the-data/',
                     target='_blank'), 
                 "", " Provides data on food scarcity across the US by county. Includes information such as \
                     poverty rate, percent of population leaving a certain distance from supermarket, \
                         percent of people receiving SNAP benefits etc ..."
            ]),
                
            html.Label([
                "",
                 html.A(
                     'Kidney Disease Surveillance System :', 
                     href='https://nccd.cdc.gov/ckd/detail.aspx?Qnum=Q705&Strat=County&Year=2018#refreshPosition',
                     target='_blank'), 
                 "", " Shows the distribution of diagnosed chronic kidney disease (CKD) among individuals aged 65 \
                     and older varies by US region. Great starting point for data analysis and modeling"
            ]),
                
            html.Label([
                "",
                 html.A(
                     'The National Kidney Foundation: ', 
                     href='https://www.kidney.org/treatment-support',
                     target='_blank'), 
                 "", " This is a great resource for people suffering with CKD. They even have a free Information helpline \
                     where patient can call to get support, ask questions to a doctor and get connected to communities"
            ]),
            
            html.Label([
                "",
                 html.A(
                     'Free Medicare Nutrition Therapy Services : ', 
                     href='https://www.medicare.gov/coverage/nutrition-therapy-services',
                     target='_blank'), 
                 "", " Following a healthy diet typically requires working with a dietician which poor people can't afford. \
                     Medicare Part B covers medical nutrition therapy services for people with diabetes or kidney disease, \
                         or people who have had a kidney transplant in the last 36 months (doctor referal needed)."
            ]),
                
            html.Label([
                "",
                 html.A(
                     'Self-Perceived Barriers and Facilitators to DASH Adherence Among Black Americans With Chronic Kidney Disease : ', 
                     href='https://www.sciencedirect.com/science/article/pii/S1051227622000887',
                     target='_blank'), 
                 "", " This information is more for researchers than patients. It's a great starting point to understand \
                     some of the disparities in CKD across US various demographics"
            ]),
            html.Label([
                "",
                 html.A(
                     'International Food Information Council : ', 
                     href='https://ific.org/media-information/press-releases/2021-food-health-survey/',
                     target='_blank'), 
                 "", " Kidney Health and Healthy Food  go together. Go here to get details on \
                     how Americans food and food purchasing decisions connect to physical health and overall wellbeing"
            ]),
            html.Label([
                "",
                 html.A(
                     'Black Health Matters : ', 
                     href='https://blackhealthmatters.com/events/',
                     target='_blank'), 
                 "", " This could be a nice point of support for African American patients. \
                     They provide various events on health outcomes such as diabetes, focussed on black communities"
            ]),
            html.Label([
                "",
                 html.A(
                     'Economic Research Service, Food & Nutrition Assitance : ', 
                     href='https://www.ers.usda.gov/topics/food-nutrition-assistance/',
                     target='_blank'), 
                 "", " This is great for researchers and data scientists who want to understand how food affects health. \
                     You can also find datasets on Supplemental Nutrition Assistance Program (SNAP) by state"
            ]),
            html.Label([
                "",
                 html.A(
                     'My Plate : ', 
                     href='https://www.myplate.gov',
                     target='_blank'), 
                 "", " Learn how to make healthy recipies. There is a free mobile app which can be downloaded on mobile   \
                     devices to track daily goals and get intructions on how to make various foods"
            ]),
            html.Label([
                "",
                 html.A(
                     'Meals on Wheels America : ', 
                     href='https://www.mealsonwheelsamerica.org/find-meals',
                     target='_blank'), 
                 "", " Find Meels on Wheels provider near you. This can be useful for people leaving in food deserts\
                     far away from supermarkets. You can enter your zip code to see Meels on Wheels providers near you."
            ]),
                
            html.Label([
                "",
                 html.A(
                     'Commodity Supplemental Food Program : ', 
                     href='https://www.fns.usda.gov/csfp/commodity-supplemental-food-program',
                     target='_blank'), 
                 "", " The Commodity Supplemental Food Program (CSFP) works to improve the health of low-income persons \
                     at least 60 years of age by supplementing their diets with nutritious USDA Foods. \
                    USDA distributes both food and administrative funds to participating states and Indian Tribal Organizations \
                        to operate CSFP"
            ]),
            html.Label([
                "",
                 html.A(
                     'SNAP Retailer Locator : ', 
                     href='https://www.fns.usda.gov/snap/retailer-locator',
                     target='_blank'), 
                 "", " This dataset provides information on SNAP authorized retailers, including their location, \
                     store type, and SNAP sales data"
            ]),
                
            html.Label([
                "",
                 html.A(
                     'FoodAPS National Household Food Acquisition and Purchase Survey : ', 
                     href='https://www.ers.usda.gov/data-products/foodaps-national-household-food-acquisition-and-purchase-survey/',
                     target='_blank'), 
                 "", " Really cool! Collects unique and comprehensive data about household food purchases and acquisitions. \
                     The survey includes nationally representative data from 4,826 households, \
                         including Supplemental Nutrition Assistance Program (SNAP) households, \
                             low-income households not participating in SNAP, and higher income households."
            ]),
                
            html.Label([
                "",
                 html.A(
                     'Senior Food Program : ', 
                     href='https://www.feedingamerica.org/our-work/hunger-relief-programs/senior-programs',
                     target='_blank'), 
                 "", " Free senior food programs are available across the country. Learn what food programs exist \
                     and where to find them in your community"
            ]),
            
            html.Label([
                "",
                 html.A(
                     'Evidence-based analysis: ', 
                     href='https://www.fns.usda.gov/research-analysis',
                     target='_blank'), 
                 "", " The Office of Policy Support (OPS) leads the development and execution of FNS's study and evaluation agenda. \
                     This web page is intended to provide access to OPS's work to program partners, other stakeholders, \
                         and the general public."
            ]),
            
            html.Label([
                "",
                 html.A(
                     'Foods Typically Purchased by Supplemental Nutrition Assistance Program (SNAP) Households: ', 
                     href='https://www.fns.usda.gov/snap/foods-typically-purchased-supplemental-nutrition-assistance-program-snap-households',
                     target='_blank'), 
                 "", " This study uses calendar year 2011 point-of-sale transaction data from a leading grocery retailer \
                     to examine the food choices of SNAP and non-SNAP households . On average, each month's transaction \
                         data contained over 1 billion records of food items bought by 26.5 million households in 127 million \
                             unique transactions."
            ]),
            
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
                ], width=10),
                
                dbc.Col([
                    html.Img(src='assets/ngslogo.png'),
                ], width=2),
                
            ], align='center'), 
            
            html.Hr(),
            html.P(
                "According to Center of Disease Control (CDC) reports, more than 15% of US adults \
                    are estimated to have CKD and 9 in 10 adults with CKD are unaware of their condition. \
                Also, African American and other minority population, mostly living in under-served c\
                    ommunities are more that 4 times as likely as Whites to develop Kidney Failure."
            ),
            
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
            #Another row
            dbc.Row([
                dbc.Col([
                    drawCorr1(object_id='corr1-id') 
                ], width=5),
                
                dbc.Col([
                    html.Label('Select Variable'),
                    dcc.Dropdown(
                        options=['Low Income', 'SNAP', 'Senior'], 
                        value='SNAP', 
                        id='var-dropdown'
                    ),
                ], width=1),
                
                dbc.Col([
                    drawCorr2(object_id='corr2-id') 
                ], width=6),
            ], align='center'),
            
            #Another row
            dbc.Row([
                dbc.Col([
                    drawSNAPSpends(object_id='snap-spend-id'),
                ], width=12),
                
            ], align='center'), 
            
            html.Br(),
            #Another row
            dbc.Row([
                dbc.Col([
                    section_resources(),
                ], width=12),
                
            ], align='center'), 
            html.Br(),
            
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


@app.callback(
    Output('corr1-id', 'figure'),
    [
     Input('var-dropdown', 'value'),
    ]
)
def update_corr1_graph(variable):
    
    
    data = corr_df1[corr_df1['Population Group']==variable]
    fig = px.bar(
        data, 
        x="Distance from supermarket", 
        y="Correlation Coeff with CKD",
        color=['blue' if x>0 else 'red' for x in data['Correlation Coeff with CKD']],
        barmode='group',
        #width=800, height=400,
        hover_data = {'p_value':True, },
        title='Correlation between CKD prevalence and access to healthy food'
    ).update(layout_showlegend=False)
    
    return fig             
   

# Run flask app
if __name__ == "__main__": 
    app.run_server(debug=False, host='0.0.0.0', port=8050)