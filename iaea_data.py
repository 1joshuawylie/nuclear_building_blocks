'''
This file stores functions related to collecting IAEA nuclear data which can be called
for other operations.

Writen by: Joshua Wylie
'''

import pandas as pd
import numpy as np
import urllib.request

# For gathering specific data from IAEA site...
def lc_pd_dataframe(url):
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    return pd.read_csv(urllib.request.urlopen(req))
# the service URL for the IAEA nuclear chart
livechart = "https://nds.iaea.org/relnsd/v0/data?"

# For collecting all ground state information in the nuclear chart
def NuChartGS():
    # Collecting all ground state data
    ground_state = lc_pd_dataframe(livechart + "fields=ground_states&nuclides=all")
    ground_state['n'] = ground_state['n'].astype(int)
    ground_state['z'] = ground_state['z'].astype(int)
    # Create html formatted name for nucleus
    ground_state['A_symbol'] = ['<sup>'+str(row['n']+row['z'])+'</sup>'+row['symbol'] for index,row in ground_state.iterrows()]

    # Dictionary to rewrite more exotic decays with their initial decay step
    decayOrder = {'EC+B+':'EC','B+P':'B+','B-N':'B-','B-2N':'B-','ECP+EC2P':'EC','2EC':'EC',
                'IT':'B-','ECP':'EC','2B+':'B+','ECSF':'SF',' ':'Not Available'} # Adjust to more common decays

    for i, row in ground_state.iterrows():
        # Convert data to log scale
        try:
            ground_state.loc[i,'log(half_life_sec)'] = np.log10(float(row['half_life_sec']))
        except:
            ground_state.loc[i,'log(half_life_sec)'] = 0
        
        # Store the more common decays in a new column
        try:
            ground_state.loc[i,'common_decays'] = decayOrder[row['decay_1']]
        except:
            ground_state.loc[i,'common_decays'] = row['decay_1']
    ground_state.loc[ground_state['half_life']=='STABLE','common_decays'] = 'Stable'
    return ground_state

def NuChartLevels(A_,symbol_):
    return lc_pd_dataframe(livechart + "fields=levels&nuclides={}{}".format(A_,symbol_))