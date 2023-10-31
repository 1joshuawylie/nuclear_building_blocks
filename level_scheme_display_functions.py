'''
This file contains:

Options for Level Scheme display:
 - plot_separation_energy:       Given an existing graph object figure, separation energy, type of nucleon, and desired color; this
                                 function plots the separation energy across the given figure at the current x and y-axis bounds

 - show_built_nucleus:           Given a header text list and image location; returns both as html.Td() and html.Img() respectively

 - drawLevel:                    Given a Plotly Graph Object, x array, list of Energy, list of half life, list of half life units;
                                 plots level scheme of all provided energies and their decay widths (if width units are in any eV)

 - plot_level_scheme:            Given a ground state dataset and level scheme dataset as pandas dataFrames; plots all levels and
                                 their decay widths along with found separation energies
    - Uses: drawLeveL(), plot_separation_energy()

 - drawGroupBox:                 Given a Plotly Graph Object, minimum X value, maximum X value, minimum Energy, maximum Energy, and an excitation ID;
                                 draws a Plotly Graph Object Scatter plot box corresponding to the excitation group spanned by the given energy (is hoverable).

 - find_best_clusters:           Given a 1D numpy array of energy levels and a desired number of clusters (default 3); finds the best
                                 cluster representation for the dataset and returns them as a list

 - plot_simplified_level_scheme: Given a ground state dataset and level scheme dataset as pandas dataFrames (and optional number of clusters);
                                 plots all levels, their decay widths, separation energies, and boxes (hoverable) for the found cluster of energies

Written by:
 - Joshua Wylie
'''

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import html, dcc
import dash_bootstrap_components as dbc

levelGroupColors = ['rgba(75, 158, 214, 0.5)','rgba(255, 157, 36, 0.5)','rgba(163, 42, 205, 0.5)','rgba(200, 0, 4, 0.5)']

def plot_separation_energy(fig_,s_,xMin,xMax,nucType,nucColor):
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
    xAxisRange = [xMin, xMax]
    try: # When we don't have a separation energy, the conversion to float will throw an error
        s_ = float(s_) * 10**-3 # Convert to MeV
        # Alternatively, if we have NaN, we can check by converting to string
        if str(s_) == 'nan':
            return None
        fig_.add_trace(go.Scatter(
            x=xAxisRange, y=[float(s_),float(s_)],
            mode='lines',
            hoverinfo='skip', # Don't provide any hover info or hover interaction from this line
            name=f'{nucType} Separation Energy',
            line=dict(color=nucColor,dash='dash'),
        ))
    except:
        return None
    return None

def drawLevel(fig_,x_,E,half_life,half_life_units,xstep=0.25):
    '''
    Given: a Plotly Graph Object, x array, list of Energy, list of half life, list of half life units
    Plots level scheme of all provided energies and their decay widths (if width units are in any eV)
    '''
    E = float(E) # In MeV
    # if half_life_units == ' ': # Old version of IAEA data, was changed to NaN
    if pd.isna(half_life_units): # Find states with unknown half life and set them to a grey line to indicate uncertain status
        fig_.add_shape(type='line',
                       x0=x_-xstep, x1=x_+xstep, y0=E, y1=E,
                       line_color='grey')
        return fig_ # Unknown half life wouldn't require any extra decay width box so we end early
    else: # Remaining 
        fig_.add_shape(type='line',
                       x0=x_-xstep, x1=x_+xstep, y0=E, y1=E,
                       line_color='white')
        
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
    
    Returns a Plotly figure of all levels with hover-able information
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
        y=levelData['energy'],
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

def drawGroupBox(fig_,minX,maxX,minE,maxE,groupID):
    fig_.add_trace(go.Scatter(
                x=[minX,minX,maxX,maxX,minX],
                y=[minE,maxE,maxE,minE,minE],
                customdata=[groupID],
                fill='toself',
                mode='lines',
                text=f'Excitation Group: {groupID}',
                hoverinfo='text',
                showlegend=False,
                fillcolor=levelGroupColors[groupID],
                line=dict(color='rgba(0, 0, 0, 0)'),  # Set line color to None (fully transparent)
            ))
    return None

from sklearn.cluster import KMeans
def find_best_clusters(data, num_clusters=3): # thanks ChatGPT!
    '''
    Finds clusters in the energy levels to best describe the generic level properties.

    Requires numpy array of level energies as an input and the desired number of clusters (default 3)
    '''
    # Reshape data into a 2D array
    data = np.array(data).reshape(-1, 1)

    # Initialize the K-Means model with the desired number of clusters
    kmeans = KMeans(n_clusters=num_clusters, random_state=0)

    # Fit the model to the data
    kmeans.fit(data)

    # Get the cluster assignments for each data point
    labels = kmeans.labels_

    # Find the cluster centers
    cluster_centers = kmeans.cluster_centers_

    # Calculate the sum of squared distances (inertia) for each cluster
    cluster_inertia = [np.sum((data[labels == i] - cluster_centers[i]) ** 2) for i in range(num_clusters)]

    # Sort the clusters by inertia in ascending order
    sorted_clusters = sorted(range(num_clusters), key=lambda i: cluster_inertia[i])

    # Select the top 3 clusters with the lowest inertia
    best_clusters = [data[labels == sorted_clusters[i]].flatten() for i in range(num_clusters)]

    return best_clusters

import textwrap
def customwrap(s,width=30):
    return "<br>".join(textwrap.wrap(s,width=width))

def plot_simplified_level_scheme(groundStateData,levelData,num_clusters=3,max_levels=50):
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
    
    (Optional) The number of clusters you wish to find

    Returns a figure of energy levels with boxes indicating the general excitation.
    '''
    levels = levelData.copy()
    n, z = levels['n'].unique()[0], levels['z'].unique()[0]
    # In the event we have tons of level data, for the sake of time, we filter out to the states with known J^\pi values (i.e. drop parenthesis values)
    if len(levels['energy']) > max_levels:
        levels = levels[levels['jp'].str.contains('\(|\)') == False]
    # If still more than max_levels levels, we will get rid of those with highest energy
    levels.sort_values('energy')
    levels = levels.head(max_levels)
    # Get initial data
    n, z = levels['n'].unique()[0], levels['z'].unique()[0]
    levels['energy'] = levels['energy'] * 10**-3

    # We want x-axis positions according to the J^\pi value
    unique_names = levels['jp'].unique() # Get unique states
    x = np.arange(len(unique_names))
    xMin, xMax = min(x)-0.5, max(x)+0.5
    # To plot each J^\pi level in their own columns, we will save them as dictionaries with x values e.g. {'0+':0,'1+':1} and {0:'0+',1:'1+'}
    name_to_position = {}
    position_to_name = {}
    for name, position in zip(unique_names, x):
        name_to_position[name] = position
        position_to_name[position] = name

    # Start plotting levels like normal...
    fig_ = go.Figure()

    try:
        # If only one level with nan energy, pass error to exception display case
        if (len(levels['energy'])==1) and (str(levels['energy'].values[0])=='nan'):
            raise ValueError
        # Draw each isotope level by iterating through each row of our levels
        for i, row in levels.iterrows():
            # Call function to draw level (note, no hover info is assigned to these levels when just drawing lines)
            fig_ = drawLevel(fig_,name_to_position[row['jp']],row['energy'],row['half_life'],row['unit_hl'])

        # Plot Separation energies
        isotope = groundStateData[(groundStateData['n']==n)&(groundStateData['z']==z)]

        # Plot separation energies
        sn = isotope['sn'].values[0] # Still in string format! Handle with function below...
        sp = isotope['sp'].values[0] # Still in string format! Handle with function below...
        plot_separation_energy(fig_,sn, xMin, xMax,'Neutron','blue')
        plot_separation_energy(fig_,sp, xMin, xMax,'Proton','red')

        full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
        # Get current y-axis ranges
        yAxisRange = full_fig.layout.yaxis.range
        rangeE = max(yAxisRange) - min(yAxisRange) # Find total energy range
        yMin, yMax = min(yAxisRange)-rangeE/10,max(yAxisRange)+rangeE/10 # set new y-axis values with offset according to extra energy range padding
        # Set new axes ranges
        fig_.update_xaxes(range=[xMin, xMax])
        fig_.update_yaxes(range=[yMin, yMax])

        # Get number of levels
        nlevels = len(levels['energy'])

        # In the event we have fewer levels than clusters, the following KMeans code would fail, so we check and adjust
        if nlevels < num_clusters:
            num_clusters = nlevels # Set cluster number equal to number of levels if too many clusters requested
        
        # Use ChatGPT assisted function to find clusters of energies
        clusters = find_best_clusters(levels['energy'].to_numpy(),num_clusters=num_clusters)
        # Sort clusters so they move in increasing order of energy
        clusters = sorted(clusters,key=sorted)
        # Iterate through cluster list to plot the boxes for each cluster
        for i in range(len(clusters)):
            # The following if statements are to set box height for each cluster considered
            if i == 0 and len(clusters) > 1: # Starting when we have more than one cluster
                minE = yMin
                maxE = max(clusters[i]) + (min(clusters[i+1]) - max(clusters[i]))/2
            elif i==0 and len(clusters) == 1: # Starting when we have exactly one cluster
                minE = yMin
                maxE = yMax
            elif i == len(clusters)-1: # Adjusting box size at last cluster
                minE = max(clusters[i-1]) + (min(clusters[i]) - max(clusters[i-1]))/2
                maxE = yMax
            else: # intermediate cluster boundaries
                minE = max(clusters[i-1]) + (min(clusters[i]) - max(clusters[i-1]))/2
                maxE = max(clusters[i]) + (min(clusters[i+1]) - max(clusters[i]))/2
            
            # Draw cluster boxes
            drawGroupBox(fig_,xMin,xMax,minE,maxE,i)

        # Display legends, axis name changes
        fig_.update_legends()
        fig_.update_layout(legend=dict(orientation='h',
                                    yanchor="bottom",y=1.0,
                                    xanchor="right",x=1))
        fig_.update_xaxes(title_text='State',
                        ticktext=list(position_to_name.values()),
                        tickvals=list(position_to_name.keys()))
        fig_.update_yaxes(title_text='Energy (MeV)')
        return fig_
    except: # In the event we have only one level and it's nan, we will need to print an exception
        wrapped_text = customwrap("Wow, it looks like there isn't any information available on this! Scientists have observed this nucleus, and are working very hard to get more information!", width=30)
        fig_.add_annotation(x=1,y=1,
                            text=wrapped_text,
                            showarrow=False)
        
        # Set new axes ranges
        fig_.update_xaxes(range=[0, 2],showticklabels=False,showgrid=False)
        fig_.update_yaxes(range=[0, 2],showticklabels=False,showgrid=False)
        return fig_
