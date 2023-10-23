'''
This file contains:

Options for Nuclear Chart display:
 - Half lives
 - Binding Energy per Nucleon
'''

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import os

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

stableVal = 31
unknownVal = 35
# Update colorbar in the following list
custom_half_life_colors = [
    [0.0, 'rgb(143, 0, 255)'],  # Violet zeptosecond
    [0.05, 'rgb(0, 0, 255)'],  # Blue attosecond
    [0.267, 'rgb(0, 255, 0)'],  # Green microsecond
    [0.375, 'rgb(255, 255, 0)'],  # Yellow megasecond (12 days)
    [0.536, 'rgb(255, 165, 0)'],  # Orange
    [0.75, 'rgb(255, 0, 0)'],  # Red
    [0.95, 'rgb(0, 0, 0)'],  # Black
    [1.0, 'rgb(200, 200, 200)'],  # Grey
]

custom_contrast_half_life_colors = [
    [0.0, 'rgb(255, 0, 0)'],  # Violet zeptosecond
    [0.95, 'rgb(0, 0, 255)'],  # Black
    [1.0, 'rgb(255, 255, 255)'],  # Grey
]

# Update colorbar in the following list
custom_binding_energy_per_nucleon_colors = [
    [0.0, 'rgb(200, 200, 200)'],  # Grey Not available
    [0.001, 'rgb(0, 0, 255)'],  # Blue at 0.0
    [0.3, 'rgb(0, 255, 0)'],  # Green at 0.2
    [0.6, 'rgb(255, 255, 0)'],  # Yellow at 0.4
    [0.8, 'rgb(255, 165, 0)'],  # Orange at 0.6
    [0.9, 'rgb(255, 0, 0)'],  # Red at 0.8
    [1.0, 'rgb(128, 0, 128)'],  # Purple at 1.0
]

custom_contrast_binding_energy_per_nucleon_colors = [
    [0.0, 'rgb(55, 55, 55)'],  # Grey Not available
    [0.001, 'rgb(255, 255, 0)'],  # Blue at 0.0
    [0.3, 'rgb(255, 0, 255)'],  # Green at 0.2
    [0.6, 'rgb(0, 0, 255)'],  # Yellow at 0.4
    [0.8, 'rgb(0, 90, 255)'],  # Orange at 0.6
    [0.9, 'rgb(0, 255, 255)'],  # Red at 0.8
    [1.0, 'rgb(127, 255, 127)'],  # Purple at 1.0
]

def half_life_plot(data_):
    '''
    Given a pandas DataFrame with the assumed columns:
     - z:                  Proton number
     - n:                  Neutron number
     - half_life:          Half life of nucleus (Used to get those nuclei with 'Stable' or no half life information available)
     - A_symbol:           HTML formatted isotope name as <sup>{A}</sup>Symbol (e.g. <sup>4</sup>He for Helium-4)
     - common_decays:      Reduced set of decay modes reducing everything to the most common mode
                           (e.g. \beta^-, \beta^+, proton, neutron, and alpha)
     - log(half_life_sec): Log of a nucleus' half life in seconds
    '''
    rows = data_['z'].unique()
    cols = data_['n'].unique()

    # Serves as the Heatmap grid spanning from minimum proton/neutron to maximum proton/neutron
    constructedMap = np.ones((len(rows),len(cols))) * np.nan # By setting all to NaN, any element with no data will be Transparent and not plotted
    dataNames = [['Unknown']*len(cols) for r in rows] # Grid to keep the names of each known isotope
    dataDecay = [['Unknown']*len(cols) for r in rows] # Grid to keep the known decay modes of each isotope

    # Populate Heatmap grid with information for stable nuclei first
    stableNuclei = data_[data_['half_life']=='STABLE'].copy()
    for i, row in stableNuclei.iterrows():
        constructedMap[row['z'],row['n']] = stableVal # Set to large log number to be effectively Stable
        dataNames[row['z']][row['n']] = row['A_symbol']
        dataDecay[row['z']][row['n']] = row['common_decays']
    
    # Populate Heatmap grid with information for nuclei with unknown half-lives
    # notAvailableNuclei = data_[data_['half_life']==' '].copy() # Old version of IAEA data, was changed to NaN
    notAvailableNuclei = data_[data_['half_life'].isna()].copy()
    for i, row in notAvailableNuclei.iterrows():
        constructedMap[row['z'],row['n']] = unknownVal # Set to large log number to be effectively unknown
        dataNames[row['z']][row['n']] = row['A_symbol']
        if isinstance(row['common_decays'], float): # For nan types
            dataDecay[row['z']][row['n']] = 'Not Available'
        else:
            dataDecay[row['z']][row['n']] = row['common_decays']

    # Populate Heatmap grid with information for all known unstable nuclei
    # unstableNuclei = data_[(data_['half_life']!='STABLE')&(data_['half_life']!=' ')].copy() # Old version of IAEA data, was changed to NaN
    unstableNuclei = data_[(data_['half_life']!='STABLE')&(data_['half_life'].notnull())].copy()
    for i, row in unstableNuclei.iterrows():
        constructedMap[row['z'],row['n']] = row['log(half_life_sec)']
        dataNames[row['z']][row['n']] = row['A_symbol']
        dataDecay[row['z']][row['n']] = row['common_decays']
    
    # Construct plotly heatmap
    chartMap = go.Heatmap(
        z=constructedMap.tolist(),
        colorscale=custom_half_life_colors,
        name='',
        xgap=0.5, # Provide slight gap between each heatmap box
        ygap=0.5, # Provide slight gap between each heatmap box
        colorbar=dict(title='log<sub>10</sub>(T<sub>1/2</sub> (s))', # Update information on the colorbar
                    len=0.7,
                    tickvals=[-21,-9,0,9,21,31,35],
                    ticktext=['zs','ns','s','Gs (or 31.7 years)','Zs (or 31.7 trillion years)','Stable (Black)','Unknown (Grey)']),
    )

    return chartMap, dataNames, dataDecay

def binding_energy_per_nucleon_plot(data_):
    '''
    Given a pandas DataFrame with the assumed columns:
     - z:                  Proton number
     - n:                  Neutron number
     - half_life:          Half life of nucleus (Used to get those nuclei with 'Stable' or no half life information available)
     - A_symbol:           HTML formatted isotope name as <sup>{A}</sup>Symbol (e.g. <sup>4</sup>He for Helium-4)
     - common_decays:      Reduced set of decay modes reducing everything to the most common mode
                           (e.g. \beta^-, \beta^+, proton, neutron, and alpha)
     - log(half_life_sec): Log of a nucleus' half life in seconds
    '''
    rows = data_['z'].unique()
    cols = data_['n'].unique()

    # Serves as the Heatmap grid spanning from minimum proton/neutron to maximum proton/neutron
    constructedMap = np.ones((len(rows),len(cols))) * np.nan # By setting all to NaN, any element with no data will be Transparent and not plotted
    dataNames = [['Unknown']*len(cols) for r in rows] # Grid to keep the names of each known isotope
    dataDecay = [['Unknown']*len(cols) for r in rows] # Grid to keep the known decay modes of each isotope

    # Get nuclei names and decay modes first:
    # Populate Heatmap grid with information for stable nuclei first
    stableNuclei = data_[data_['half_life']=='STABLE'].copy()
    for i, row in stableNuclei.iterrows():
        dataNames[row['z']][row['n']] = row['A_symbol']
        dataDecay[row['z']][row['n']] = row['common_decays']
    
    # Populate Heatmap grid with information for nuclei with unknown half-lives
    # notAvailableNuclei = data_[data_['half_life']==' ']
    notAvailableNuclei = data_[data_['half_life'].isna()].copy()
    for i, row in notAvailableNuclei.iterrows():
        dataNames[row['z']][row['n']] = row['A_symbol']
        dataDecay[row['z']][row['n']] = 'Not Available'

    # Populate Heatmap grid with information for all known unstable nuclei
    # unstableNuclei = data_[(data_['half_life']!='STABLE')&(data_['half_life']!=' ')] # Old version of IAEA data, was changed to NaN
    unstableNuclei = data_[(data_['half_life']!='STABLE')&(data_['half_life'].notnull())].copy()
    for i, row in unstableNuclei.iterrows():
        dataNames[row['z']][row['n']] = row['A_symbol']
        dataDecay[row['z']][row['n']] = row['common_decays']
    
    # Get known binding energy per nucleon for each known value
    # knownNuclei = data_[data_['binding']!=' '] # Old version of IAEA data, was changed to NaN
    knownNuclei = data_[data_['binding'].notnull()]
    for i, row in knownNuclei.iterrows():
        constructedMap[row['z'],row['n']] = float(row['binding'])
    # Get nuclei with unknown binding energy per nucleon
    # unknownNuclei = data_[data_['binding']==' '] # Old version of IAEA data, was changed to NaN
    unknownNuclei = data_[data_['binding'].isna()]
    for i, row in unknownNuclei.iterrows():
        constructedMap[row['z'],row['n']] = -10 # For unknown nuclei
    # Construct plotly heatmap
    chartMap = go.Heatmap(
        z=constructedMap.tolist(),
        colorscale=custom_binding_energy_per_nucleon_colors,
        name='',
        xgap=0.5, # Provide slight gap between each heatmap box
        ygap=0.5, # Provide slight gap between each heatmap box
        colorbar=dict(title='Binding Energy per Nucleon (BE/A) (keV))', # Update information on the colorbar
                    len=0.7,
                    # tickvals=[-21,-9,0,9,21,31,35],
                    # ticktext=['zs','ns','s','Gs (or 31.7 years)','Zs (or 31.7 trillion years)','Stable (Black)','Unknown (Grey)']
                    ),
    )

    return chartMap, dataNames, dataDecay

def drawMagicNumbers(fig_,xRange,yRange,xoffset,yoffset):
    # Draw magic number boxes and images of tiles
    magicNumbers = [2, 8, 20, 28, 50, 82, 126]
    # store current values of magic numbers that fall within given range
    neutronMagic = [m for m in magicNumbers if (m >= min(xRange)) and (m <= max(xRange))]
    protonMagic = [m for m in magicNumbers if (m >= min(yRange)) and (m <= max(yRange))]

    for nm in neutronMagic:
        fig_.add_shape(type='rect',
            x0=nm-0.5,x1=nm+0.5,y0=min(yRange)+yoffset,y1=max(yRange)+0.5,
            opacity=0.5,layer='below',fillcolor='grey',line_width=0
        )
        if max(xRange) < 50:
            fig_.add_layout_image(
                dict(
                    source=f'assets/shell_closure_{nm}.png',
                    xref="x",
                    yref="y",
                    x=nm,
                    y=min(yRange)+0.5,
                )
            )
    for pm in protonMagic:
        fig_.add_shape(type='rect',
            x0=min(xRange)+xoffset,x1=max(xRange)+0.5,y0=pm-0.5,y1=pm+0.5,
            opacity=0.5,layer='below',fillcolor='grey',line_width=0
        )
        if max(yRange) < 50:
            fig_.add_layout_image(
                dict(
                    source=f'assets/shell_closure_{pm}.png',
                    xref="x",
                    yref="y",
                    x=min(xRange),
                    y=pm
                )
            )
    
    fig_.update_layout_images(dict(
        sizex=1,
        sizey=1,
        xanchor="center",
        yanchor="middle"
    ))

def separateSymAndA(string_):
    '''Given a string containing a nucleus format {A}{Symbol} (e.g. 12C) returns the A and Symbol as a list [A, symbol] of types [int, str]'''
    sym = ''
    A = ''
    for i in string_:
        if i.isdigit():
            A += i
        else:
            sym += i
    return [int(A), sym]

def show_user_made_nuclei(fig_,chartData):
    # List all found image files in 'assets/Approved_Pictures'
    picturePath = 'assets/Approved_Pictures'
    listPictures = [f for f in os.listdir(picturePath) if os.path.isfile(os.path.join(picturePath,f))]
    # Split before the excitation number by keeping the first list element of a split('_') string
    listNuclei = [ln.split('_')[0] for ln in listPictures]
    listASym = [separateSymAndA(s) for s in listNuclei]
    uniqueASym = pd.DataFrame(listASym,columns=['A','symbol'])
    noDuplicatesASym = uniqueASym.drop_duplicates(keep='first')

    # Get z for uniqueASym which removed duplicate entries from ground state data
    for i, row in noDuplicatesASym.iterrows():
        rowGS = chartData[chartData['symbol']==row['symbol']]
        # print(rowGS['z'].unique().size==0)
        if rowGS['z'].unique().size==0:
            print('continuing')
            continue
        
        noDuplicatesASym.loc[i,'z'] = rowGS['z'].unique()
    noDuplicatesASym['n'] = noDuplicatesASym['A'] - noDuplicatesASym['z']
    
    fig_.add_trace(go.Scatter(
        x=noDuplicatesASym['n'],
        y=noDuplicatesASym['z'],
        mode='markers',
        hoverinfo='skip',
        showlegend=False,
        marker=dict(
            color='#00d4ff',
            symbol='diamond'
        )
    ))
