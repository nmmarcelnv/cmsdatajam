import pandas as pd
import numpy as np

def get_ckd_by_counties()

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
    ckd = pd.read_csv('https://raw.githubusercontent.com/nmmarcelnv/cmsdatajam/main/data/Prevalence_of_CKD_by_US_State_and_County_by_County_2019.csv')
    
    #https://towardsdatascience.com/the-ultimate-state-county-fips-tool-1e4c54dc9dff
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
    
    #a copy is saved as parquet in the git repos: 
    #https://github.com/nmmarcelnv/cmsdatajam/blob/main/data/ckd_by_county.parquet
    df = pd.merge(ckd, fips,on=['state','county'])
    
    return df

