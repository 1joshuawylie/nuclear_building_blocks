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

############ Level Scheme #############
level_scheme = dbc.Card(
    [
        dbc.Label(id='display_level_nucleus_name'),
        ########## Level Scheme and Built Nuclei Images Block ###########
        dcc.Graph(
            id='level_scheme'
        )
    ]
)
############ Level Scheme / Images of User "Discovered" Nuclei #############
built_nucleus_images = dbc.Card(
    [
        dbc.Label(id='display_built_nucleus_name'),
        ########## Level Scheme and Built Nuclei Images Block ###########
        dbc.Card(
            id='block_built_nucleus'
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
            html.Br(),
            dbc.Row([
                dbc.Col([
                    level_scheme
                ], width=6),
                dbc.Col([
                    built_nucleus_images
                ], width=6),
            ], align='center'),      
        ]), color = 'dark'
    )
])



# Plotting functions which will be used below
def plot_separation_energy(fig_,s_,nucType,nucColor):
    try: # When we don't have a separation energy, the conversion to float will throw an error
        s_ = float(s_) * 10**-3 # Convert to MeV
        full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
        xAxisRange = full_fig.layout.xaxis.range
        print(xAxisRange)
        fig_.add_trace(go.Scatter(
            x=xAxisRange, y=[float(s_),float(s_)],
            mode='lines',
            hoverinfo='skip', # Don't provide any hover info or hover interaction from this line
            name=f'{nucType} Separation Energy',
            line=dict(color=nucColor,dash='dash')
        ))
    except:
        print('printing exception')
        fig_.add_annotation(
            xref="paper",
            yref="paper",
            showarrow=False,
            xanchor='left',
            x=0.01,
            y=0.95,
            text=f'No {nucType} Separation Energy Found'
        )
    return None

def show_built_nucleus(headerText,imageLoc):
    # builtNucleusPicture = html.Div(children=[
    #     html.Td(headerText),
    #     html.Img(src=imageLoc,style={'height':'50%'})
    # ])
    # return builtNucleusPicture
    builtNucleusHeader = html.Td(headerText)
    builtNucleusPicture = html.Img(src=imageLoc)#,style={'height':'30vh'})
    return builtNucleusHeader, builtNucleusPicture

def drawLevel(fig_,x_,E,half_life,half_life_units,xstep=0.25):
    E = float(E) *10**-3 # Convert from keV to MeV
    if half_life_units == ' ':
        fig_.add_shape(type='line',
                       x0=x_-xstep, x1=x_+xstep, y0=E, y1=E,
                       line_color='grey')
    elif half_life == 'STABLE':
        fig_.add_shape(type='line',
                       x0=x_-xstep, x1=x_+xstep, y0=E, y1=E,
                       line_color='black')
    else:
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

def plot_level_scheme():
    global isotopeLevels
    # Get initial data
    n, z = isotopeLevels['n'].unique()[0], isotopeLevels['z'].unique()[0]
    symbol = isotopeLevels['symbol'].unique()[0]
    A = n + z

    fig_ = go.Figure()
    # We want positions according to the J^\pi value
    unique_names = isotopeLevels['jp'].unique()
    x = np.arange(len(unique_names))
    name_to_position = {}
    position_to_name = {}
    for name, position in zip(unique_names, x):
        name_to_position[name] = position
        position_to_name[position] = name

    # Draw each isotope level
    for i, row in isotopeLevels.iterrows():
        fig_ = drawLevel(fig_,name_to_position[row['jp']],row['energy'],row['half_life'],row['unit_hl'])
        isotopeLevels.loc[i,'x_index'] = name_to_position[row['jp']]
    # get header information for considered nucleus
    headerText_ = html.Td(['Level scheme for your selected nucleus: ',
                            html.Sup(str(A)), symbol])
                            # html.Br(),'Only showing levels with known half-life units.'])
    
    # Scatter plot of positions for hover information
    fig_.add_trace(go.Scatter(
        x=isotopeLevels['x_index'],
        y=isotopeLevels['energy']*10**-3,
        mode="markers",
        name='States',
        marker_size=0.001,
        showlegend=False
    ))

    # Plot Separation energies
    isotope = ground_state[(ground_state['n']==n)&(ground_state['z']==z)].copy()
    sn = isotope['sn'].values[0] # Still in string format! Handle with function below...
    sp = isotope['sp'].values[0] # Still in string format! Handle with function below...
    plot_separation_energy(fig_,sn,'Neutron','blue')
    plot_separation_energy(fig_,sp,'Proton','red')
    fig_.update_legends()
    fig_.update_xaxes(title_text='State',
                      ticktext=list(position_to_name.values()),
                      tickvals=list(position_to_name.keys()))
    fig_.update_yaxes(title_text='Energy (MeV)')
    return fig_, headerText_


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

    if chart_type_name == 'Half Life':
        custom_colors = [
            [0.0, 'rgb(0, 0, 255)'],  # Blue at 0.0
            [0.4, 'rgb(0, 255, 0)'],  # Green at 0.2
            [0.5, 'rgb(255, 255, 0)'],  # Yellow at 0.4
            [0.6, 'rgb(255, 165, 0)'],  # Orange at 0.6
            [0.8, 'rgb(255, 0, 0)'],  # Red at 0.8
            [0.95, 'rgb(0, 0, 0)'],  # Black at 0.999
            [1.0, 'rgb(200, 200, 200)'],  # Grey at 0.0
        ]

        rows = currentData['z'].unique()
        cols = currentData['n'].unique()
        constructedMap = np.ones((len(rows),len(cols))) * np.nan
        dataNames = [['Unknown']*len(cols) for r in rows]
        dataDecay = [['Unknown']*len(cols) for r in rows]

        stableNuclei = currentData[currentData['half_life']=='STABLE']
        for i, row in stableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = 31 # Set to large log number to be effectively Stable
            dataNames[row['z']][row['n']] = row['A_symbol']
            dataDecay[row['z']][row['n']] = row['common_decays']
        
        notAvailableNuclei = currentData[currentData['half_life']==' ']
        for i, row in notAvailableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = 35 # Set to large log number to be effectively unknown
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
                        tickvals=[-21,-9,0,9,21,31,35],
                        ticktext=['zs','ns','s','Gs (or 31.7 years)','Zs (or 31.7 trillion years)','Stable (Black)','Unknown (Grey)'])
        )

        chart.add_traces([unstableMap])#,stableMap])
        # chart.add_traces([stableMap])
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


#### Level chart ####
@callback(
    Output('level_scheme','figure'),
    Output('display_level_nucleus_name','children'),
    Output('display_built_nucleus_name','children'),
    Output('block_built_nucleus','children'),
    Input('nuclear_chart','clickData'),
    Input('level_scheme','hoverData')
)
def update_level_scheme(clickData, hoverData):
    global isotopeLevels # Modify global variable of isotope levels
    dump = json.loads(json.dumps(clickData))
    dumpHover = json.loads(json.dumps(hoverData))
    triggerID = ctx.triggered_id
    # print('Trigger ID: ',triggerID)

    # When we click on a new nucleus on the nuclear, load the corresponding level data
    if triggerID == 'nuclear_chart':
        # print('Click dump: ',dump)
        nucDataDict = dump['points'][0]
        n, z = nucDataDict['x'], nucDataDict['y']
        # print('Triggered Dict: ',nucDataDict)
        element = ground_state.loc[(ground_state['z']==z)] # Get element chain data
        isotope = element[element['n']==n] # Get specific isotope data
        symbol = isotope['symbol'].values[0] # Get corresponding symbol name for element
        A = n + z
        
        # Get level data and plot levels
        isotopeLevels = iaea.NuChartLevels(A,symbol)
    
    # Plotting level scheme
    # levels = go.Figure()
    imagePath = 'assets/'
    if triggerID is None:
        levels = go.Figure()
        levels.add_trace(go.Scatter(
            x=[1],
            y=[1],
            text=["Please click a nucleus to see its levels"],
            mode="text",
            hoverinfo='skip',
        ))
        levels.update_yaxes(showticklabels=False,showgrid=False)
        levels.update_xaxes(showticklabels=False,showgrid=False)
        # Default header information 
        headerText = html.Td(['Level scheme for your selected nucleus: '])
        text = ['Please select a nucleus to see a block version of it: ']
        image = imagePath + 'logo.png'
        builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,image)
        # builtNucleusHeader, builtNucleusPicture = html.Div(children=[
        #     html.Td(['Please select a nucleus to see a block version of it: ']),
        #     html.Img(src=imagePath + 'bing_image_creator_atomic_nucleus.jpg')
        # ])
    elif triggerID == 'nuclear_chart':
        levels, headerText = plot_level_scheme()

        # For showing picture of built nucleus
        pictureFile = imagePath + str(A) + symbol + '_0.png'
        if not os.path.isfile(pictureFile):
            text = ['Hey, it looks like no one has discovered this state yet!\nUpload a picture of your\'s by following this code...']
            image = imagePath + 'bing_image_creator_halo_prompt.jpg'
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,image)
        else:
            text = ['You\'re currently looking at the ground state of: ',
                    html.Sup(str(A)), symbol]
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,pictureFile)

    elif triggerID == 'level_scheme':
        levels, headerText = plot_level_scheme()

        # print('dumpHover: ',dumpHover)
        # print('Isotope levels: ',isotopeLevels.columns)
        A = isotopeLevels['n'].unique()[0] + isotopeLevels['z'].unique()[0]
        symbol = isotopeLevels['symbol'].unique()[0]
        excitation = dumpHover['points'][0]['pointIndex']
        # For showing picture of built nucleus
        pictureFile = imagePath + str(A) + symbol + f'_{excitation}' + '.png'
        if not os.path.isfile(pictureFile):
            text = ['Hey, it looks like no one has discovered this state yet!\nUpload a picture of your\'s by following this code...']
            image = imagePath + 'bing_image_creator_halo_prompt.jpg'
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,image)
        else:
            text = ['You\'re currently looking at the excited  of: ',
                    html.Sup(str(A)), symbol]
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,pictureFile)
    return levels, headerText, builtNucleusHeader, builtNucleusPicture






# Run app...
if __name__ == '__main__':
    app.run(debug=True)