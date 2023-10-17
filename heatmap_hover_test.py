# This will likely need to be divided into other functions later. just getting things set up

# Handle data effectively
import pandas as pd
import numpy as np
import os
import iaea_data as iaea # importing iaea data

import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from dash import Dash, dcc, html, Input, Output, State, callback
from dash import ctx # Used for identifying callback_context
import dash_daq as daq
import dash_bootstrap_components as dbc
import json

# Custom dash functions
import nuclear_chart_views as ncv

# Call ground state information
ground_state = iaea.NuChartGS()
# Call specific level scheme
isotopeLevels = None # Initialize a global variable to cut down on the number of reloads required to look at a nucleus level scheme

def normalCol(dfCol):
    # Normalizes a give dataframe column
    return (dfCol - dfCol.min()) / (dfCol.max() - dfCol.min())
decayColor = {'B-':'skyblue','Stable':'black','N':'royalblue','2N':'blue','P':'deeppink','A':'yellow',
              'EC':'palevioletred','2P':'red','B+':'pink','2B-':'darkviolet','SF':'lime','Not Available':'grey'}

# Begin dash layout design
app = Dash(__name__,external_stylesheets=[dbc.themes.SLATE])
# app = Dash(__name__,meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])


########## View type / Chart Manipulation and Nuclear Chart Block ##########
chart_options = dbc.Card(
    [
        #### Options and View Type ####
        dbc.Card(
            [
                ##### View Type #####
                dbc.Label('Please select your desired view:'),
                dcc.Dropdown(
                    ['Half Life', 'Main Decay Mode'],
                    'Half Life',
                    id='chart_type'
                )
            ]),
        dbc.Card(
            [
                ##### Proton Slider #####
                dbc.Label('Show Proton Range:'),
                dcc.Slider(
                    ground_state['z'].min(),
                    ground_state['z'].max(),
                    step=None,
                    id='proton_axis_slider',
                    value=ground_state['z'].max()
                )
            ]),
        dbc.Card(
            [
                ##### Neutron Slider #####
                dbc.Label('Show Proton Range:'),
                dcc.Slider(
                    ground_state['n'].min(),
                    ground_state['n'].max(),
                    step=None,
                    id='neutron_axis_slider',
                    value=ground_state['n'].max()
                ),
                ##### Extra Clickable Options #####
            ],
        )
    ]
)
chart_plot = dbc.Card(
    [
        ########### Nuclear Chart ###########
        dcc.Graph(
            id='nuclear_chart',style={'height':'50vh'}
        )
    ]
)


app.title = 'Interactive Nuclear Chart'

# Begin describing the layout of the figure from top down...
app.layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    chart_options
                ], width=3),
                dbc.Col([
                    chart_plot
                ], width=9),
            ], align='center'),      
        ]), color = 'dark'
    )
])



# Now set any necessary callbacks corresponding to the ids given in the layout section
@callback(
    Output('nuclear_chart','figure'),
    Input('chart_type','value'),
    Input('neutron_axis_slider','value'),
    Input('proton_axis_slider','value')
)
def update_chart_type(chart_type_name,neutron_slider,proton_slider):
    currentData = ground_state.loc[(ground_state['n']<=neutron_slider)&(ground_state['z']<=proton_slider),:].copy()
    xrange = [min(currentData['n']), max(currentData['n'])]
    yrange = [min(currentData['z']), max(currentData['z'])]
    chart = go.Figure()

    custom_colors = [
        [0.0, 'rgb(0, 0, 255)'],  # Blue at 0.0
        [0.4, 'rgb(0, 255, 0)'],  # Green at 0.2
        [0.5, 'rgb(255, 255, 0)'],  # Yellow at 0.4
        [0.6, 'rgb(255, 165, 0)'],  # Orange at 0.6
        [0.8, 'rgb(255, 0, 0)'],  # Red at 0.8
        [0.95, 'rgb(0, 0, 0)'],  # Black at 0.999
        [1.0, 'rgb(200, 200, 200)'],  # Grey at 0.0
    ]

    if chart_type_name == 'Half Life':
        rows = currentData['z'].unique()
        cols = currentData['n'].unique()
        constructedMap = np.ones((len(rows),len(cols))) * np.nan
        dataNames = [['Unknown']*len(cols) for r in rows]
        # dataNames[:,:] = 'Nonexistent'
        dataDecay = [['Unknown']*len(cols) for r in rows]
        # dataDecay[:,:] = 'Nonexistent'

        stableNuclei = currentData[currentData['half_life']=='STABLE']
        for i, row in stableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = 31 # Set to large log number to be effectively Stable
            dataNames[row['z']][row['n']] = row['A_symbol']
            dataDecay[row['z']][row['n']] = row['common_decays']
        
        notAvailableNuclei = currentData[currentData['half_life']==' ']
        for i, row in notAvailableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = 34 # Set to large log number to be effectively unknown
            dataNames[row['z']][row['n']] = row['A_symbol']
            dataDecay[row['z']][row['n']] = 'Data not available'

        # Recreate the map
        # constructedMap = np.ones((len(rows),len(cols))) * np.nan
        unstableNuclei = currentData[(currentData['half_life']!='STABLE')&(currentData['half_life']!=' ')]
        unstableNuclei['normalized_log_half_life_sec'] = normalCol(unstableNuclei['log(half_life_sec)'])
        for i, row in unstableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = row['log(half_life_sec)']
            dataNames[row['z']][row['n']] = row['A_symbol']
            dataDecay[row['z']][row['n']] = row['common_decays']
        
        unstableMap = go.Heatmap(
            z=constructedMap.tolist(),
            colorscale=custom_colors,
            name='',
            xgap=0.5, # Provide slight gap between each heatmap box
            ygap=0.5, # Provide slight gap between each heatmap box
            colorbar=dict(title='log<sub>10</sub>(T<sub>1/2</sub> (s))', # Update information on the colorbar
                        len=0.7,
                        tickvals=[-21,-9,0,9,21,31,34],
                        ticktext=['zs','ns','s','Gs (or 31.7 years)','Zs (or 31.7 trillion years)','Stable (Black)','Unknown (Grey)'])
        )

        chart.add_traces([unstableMap])#,stableMap])
    # ADD IF STATEMENTS FOR OTHER CHART TYPES HERE AND BE SURE TO INCLUDE IT IN THE DROPDOWN MENU IN THE LAYOUT ABOVE
    # elif chart_type_name == 'Main Decay Mode':
    chart.update_xaxes(title_text='Number of Neutrons',showspikes=True,range=xrange)
    chart.update_yaxes(title_text='Number of Protons',showspikes=True,range=yrange,automargin=True)
    chart.update_layout(yaxis_scaleanchor='x') # Fix aspect ratio
    chart.update_traces(customdata=np.dstack((dataNames,dataDecay)),
                        hovertemplate='%{customdata[0]}<br>' + # Uses data from dataNames argument above
                '%{x} Neutrons<br>' + # Uses data from dataNeutr argument above
                '%{y} Protons<br>' + # Uses data from dataProto argument above
                '%{customdata[1]} Decay Mode<br>', # Uses data from dataProto argument above
                ) # For click data info
    return chart



# Run app...
if __name__ == '__main__':
    app.run(debug=True)