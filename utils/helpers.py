import pandas as pd
import numpy as np

def prepare_modeling_data()

    dtypes = {
        'StateFIPS':str,
        'CountyFIPS_3':str,
        'CountyName':str,
        'StateName':str,
        'CountyFIPS':str,
        'StateAbbr':str,
        'STATE_COUNTY':str
    }
    
    #original source : https://nccd.cdc.gov/ckd/detail.aspx?Qnum=Q705&Strat=County&Year=2018#refreshPosition
    ckd = pd.read_parquet('https://github.com/nmmarcelnv/cmsdatajam/blob/main/data/Prevalence_of_CKD_by_US_State_and_County_by_County_2019.parquet?raw=true')
    ckd.columns = ['CkdRate','County','State','Year']
    ckd = ckd[['County','State','Year','CkdRate']]
    ckd['County'] = ckd['County'].str.upper()
    ckd['State'] = ckd['State'].str.upper()
    
    #https://towardsdatascience.com/the-ultimate-state-county-fips-tool-1e4c54dc9dff
    
    fips = pd.read_csv(
        'https://raw.githubusercontent.com/ChuckConnell/articles/master/fips2county.tsv', 
        sep='\t', 
        usecols=['CountyName','StateName','CountyFIPS','StateAbbr'],
        dtype=dtypes
    )
    fips.columns=['County','State','FIPS', 'StateAbr']
    fips = fips[['State','StateAbr','County','FIPS']]
    fips['County'] = fips['County'].str.upper()
    fips['State'] = fips['State'].str.upper()


    unemp_df = pd.read_csv("https://raw.githubusercontent.com/plotly/datasets/master/fips-unemp-16.csv",dtype={"fips": str})
    unemp_df['unemp'] = (unemp_df['unemp']/unemp_df['unemp'].max()) *(100)
    unemp_df = unemp_df.rename(columns={'fips':'FIPS', 'unemp':'unEmpRate'})
    
    return df


def get_povertyrate_by_county():
    
    data_atlas_link = 'https://www.ers.usda.gov/webdocs/DataFiles/80591/FoodAccessResearchAtlasData2019.xlsx?v=9165.3'
    usecols = ['State','County','LILATracts_Vehicle', 'HUNVFlag', 'LowIncomeTracts', 'PovertyRate', 'MedianFamilyIncome']
    dfatlas = pd.read_excel(data_atlas_link,sheet_name='Food Access Research Atlas', usecols=usecols)

    dfatlas['State'] = dfatlas['State'].str.upper()
    dfatlas['County'] = dfatlas['County'].apply(lambda x: x.upper().replace(' COUNTY','').strip())

    dtypes = {
        'StateFIPS':str, 
        'CountyFIPS_3':str, 
        'CountyName':str, 
        'StateName':str, 
        'CountyFIPS':str,
        'StateAbbr':str, 
        'STATE_COUNTY':str
    }

    fips = pd.read_csv(
        'https://raw.githubusercontent.com/ChuckConnell/articles/master/fips2county.tsv',
        sep='\t', 
        usecols=['CountyName','StateName','CountyFIPS','StateAbbr'],              
        dtype=dtypes
    )

    fips.columns=['County','State','FIPS', 'State3']
    fips = fips[['State','County','FIPS', 'State3']]
    fips['State'] = fips['State'].str.upper()
    fips['County'] = fips['County'].str.upper()

    dff = pd.merge(
        dfatlas,
        fips.drop_duplicates(),
        on=['State', 'County'],
    )
    #save as dff.to_parquet('../data/FoodAccessResearchAtlasData2019.parquet')
    
    return dff