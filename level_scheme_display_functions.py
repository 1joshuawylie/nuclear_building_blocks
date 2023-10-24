'''
This file contains:

Options for Level Scheme display:
 - drawLevel:              
 - plot_separation_energy: Given an existing graph object figure, separation energy, type of nucleon, and desired color; this function
                           plots the separation energy across the given figure at the current x and y-axis bounds
 - plot_level_scheme:      Iterates over given dataset and plots all levels and their decay widths along with found separation energies
    - Uses: drawLeveL(), plot_separation_energy()
'''

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html

def plot_separation_energy(fig_,s_,nucType,nucColor):
    '''
    Given a pandas DataFrame with the assumed columns:
     - z:                  Proton number
     - n:                  Neutron number
     - jp:
     - energy:
     - half_life:          Half life of nucleus (Used to get those nuclei with 'Stable' or no half life information available)
     - unit_hl:
     - A_symbol:           HTML formatted isotope name as <sup>{A}</sup>Symbol (e.g. <sup>4</sup>He for Helium-4)
     - common_decays:      Reduced set of decay modes reducing everything to the most common mode
                           (e.g. \beta^-, \beta^+, proton, neutron, and alpha)
     - log(half_life_sec): Log of a nucleus' half life in seconds
    '''
    try: # When we don't have a separation energy, the conversion to float will throw an error
        s_ = float(s_) * 10**-3 # Convert to MeV
        full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
        xAxisRange = full_fig.layout.xaxis.range
        fig_.add_trace(go.Scatter(
            x=xAxisRange, y=[float(s_),float(s_)],
            mode='lines',
            hoverinfo='skip', # Don't provide any hover info or hover interaction from this line
            name=f'{nucType} Separation Energy',
            line=dict(color=nucColor,dash='dash'),
        ))
    except:
        full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
        xAxisRange = full_fig.layout.xaxis.range
        yAxisRange = full_fig.layout.yaxis.range
        yDiff = (max(yAxisRange)-min(yAxisRange))/100
        fig_.add_annotation(
            showarrow=False,
            yanchor="bottom",y=max(yAxisRange)-yDiff,
            xanchor="right",x=max(xAxisRange),
            text=f'No {nucType} Separation Energy Found'
        )
    return None

def show_built_nucleus(headerText,imageLoc):
    builtNucleusHeader = html.Td(headerText)
    builtNucleusPicture = html.Img(src=imageLoc,style={'height':'45vh'})
    return builtNucleusHeader, builtNucleusPicture

def drawLevel(fig_,x_,E,half_life,half_life_units,xstep=0.25):
    '''
    Given: a Plotly Graph Object, x array, list of Energy, list of half life, list of half life units
    Plots level scheme of all provided energies and their decay widths (if width units are in any eV)
    '''
    E = float(E) *10**-3 # Convert from keV to MeV
    # if half_life_units == ' ': # Old version of IAEA data, was changed to NaN
    if pd.isna(half_life_units): # Find states with unknown half life and set them to a grey line to indicate uncertain status
        fig_.add_shape(type='line',
                       x0=x_-xstep, x1=x_+xstep, y0=E, y1=E,
                       line_color='grey')
        return fig_ # Unknown half life wouldn't require any extra decay width box so we end early
    else: # Remaining 
        fig_.add_shape(type='line',
                       x0=x_-xstep, x1=x_+xstep, y0=E, y1=E,
                       line_color='black')
        
        # For states with a noticable decay width (keV, MeV, etc.)
        if 'eV' in half_life_units:
            convertEV = {'eV':10**-6,'keV':10**-3,'MeV':1}
            G = float(half_life) * convertEV[half_life_units.replace(' ','')]
            fig_.add_shape(type='rect',
                           x0=x_-xstep, x1=x_+xstep, y0=E-G/2, y1=E+G/2,
                           line_width=0, fillcolor='grey', opacity=0.25)
    return fig_

def plot_level_scheme(groundStateData,levelData):
    '''
    Given two pandas DataFrames, groundStateData and levelData, which must contain the columns:
    
    groundStateData:
     - z:  Proton number
     - n:  Neutron number
     - sp: Proton Separation Energies
     - sn: Neutron Separation Energies
    
    levelData:
     - z:         Proton number
     - n:         Neutron number
     - jp:        J^\pi value associated with each level
     - energy:    Energy of level
     - half_life: Half life of nucleus (Used to get those levels with sizeable decay widths on the order of keV or greater for band plot)
     - unit_hl:   Units of half life used to determine which decay widths are sizeable (and worth plotting the decay width band)
    '''
    # Get initial data
    n, z = levelData['n'].unique()[0], levelData['z'].unique()[0]

    fig_ = go.Figure()
    # We want positions according to the J^\pi value
    unique_names = levelData['jp'].unique()
    x = np.arange(len(unique_names))
    # To plot each J^\pi level in their own columns, we will save them as dictionaries with x values e.g. {'0+':0,'1+':1} and {0:'0+',1:'1+'}
    name_to_position = {}
    position_to_name = {}
    for name, position in zip(unique_names, x):
        name_to_position[name] = position
        position_to_name[position] = name

    # Draw each isotope level
    for i, row in levelData.iterrows():
        fig_ = drawLevel(fig_,name_to_position[row['jp']],row['energy'],row['half_life'],row['unit_hl'])
        levelData.loc[i,'x_index'] = name_to_position[row['jp']]
    
    # Scatter plot of positions for hover information
    fig_.add_trace(go.Scatter(
        x=levelData['x_index'],
        y=levelData['energy']*10**-3,
        mode="markers",
        name='States',
        marker_size=0.001,
        showlegend=False
    ))

    # Plot Separation energies
    isotope = groundStateData[(groundStateData['n']==n)&(groundStateData['z']==z)]

    full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
    # Get current axes ranges
    xAxisRange = full_fig.layout.xaxis.range
    yAxisRange = full_fig.layout.yaxis.range
    # Set new axes ranges
    fig_.update_xaxes(range=[min(xAxisRange)-0.25,max(xAxisRange)+0.25])
    fig_.update_yaxes(range=[min(yAxisRange)-0.1,max(yAxisRange)+0.1])

    # Plot separation energies
    sn = isotope['sn'].values[0] # Still in string format! Handle with function below...
    sp = isotope['sp'].values[0] # Still in string format! Handle with function below...
    plot_separation_energy(fig_,sn,'Neutron','blue')
    plot_separation_energy(fig_,sp,'Proton','red')

    # Display legends, axis name changes
    fig_.update_legends()
    fig_.update_layout(legend=dict(orientation='h',
                                   yanchor="bottom",y=1.02,
                                   xanchor="right",x=1))
    fig_.update_xaxes(title_text='State',
                      ticktext=list(position_to_name.values()),
                      tickvals=list(position_to_name.keys()))
    fig_.update_yaxes(title_text='Energy (MeV)')
    return fig_