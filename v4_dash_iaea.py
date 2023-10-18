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

def oxfordComma(_s):
    # Thanks stackoverflow!: https://stackoverflow.com/questions/53981845/grammatically-correct-human-readable-string-from-list-with-oxford-comma
    if len(_s) < 3:
        return ' and '.join(map(str, _s))
    *a, b = _s
    return f"{', '.join(map(str, a))}, and {b}"


def collaboratorNames(string_):
    # Assumes string is the file name of the nucleus
    names = string_.split('-')[-1] # According to naming convention {A}{sym}_{exc}-{name1};{name2}.png, names is the last part split
    names = names.split('.')[0] # Eliminate the file type suffix
    names = names.replace('_',' ')
    listNames = names.split(';')

    return oxfordComma(listNames)

decayColor = {'B-':'skyblue','Stable':'black','N':'royalblue','2N':'blue','P':'deeppink','A':'yellow',
              'EC':'palevioletred','2P':'red','B+':'pink','2B-':'darkviolet','SF':'lime','Not Available':'grey'}

# Begin dash layout design
app = Dash(__name__,external_stylesheets=[dbc.themes.SLATE])
# app = Dash(__name__,meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])


########## View type / Chart Manipulation and Nuclear Chart Block ##########
chart_options = dbc.Offcanvas(
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
                    # value=ground_state['z'].max()
                    value=21
                )
            ]),
        dbc.Card(
            [
                ##### Neutron Slider #####
                dbc.Label('Show Neutron Range:'),
                dcc.Slider(
                    ground_state['n'].min(),
                    ground_state['n'].max(),
                    step=None,
                    id='neutron_axis_slider',
                    # value=ground_state['n'].max()
                    value=28
                ),
                ##### Extra Clickable Options #####
            ],
        )
    ],
    id='offcanvas',
    is_open=False,
    title='Nuclear Chart Options'
)
chart_plot = dbc.Card(
    [
        ########### Nuclear Chart ###########
        dcc.Graph(
            id='nuclear_chart',style={'height':'80vh'}
        )
    ]
)

############ Level Scheme #############
level_scheme = dbc.Card(
    [
        # dbc.Label(id='display_level_nucleus_name'),
        ########## Level Scheme and Built Nuclei Images Block ###########
        dcc.Graph(
            id='level_scheme',style={'height':'45vh'}
        ),
    ]
)
############ Level Scheme / Images of User "Discovered" Nuclei #############
built_nucleus_images = dbc.Card(
    [
        dbc.Label(id='display_built_nucleus_name'),
        ########## Level Scheme and Built Nuclei Images Block ###########
        dcc.Loading(id='loading_level_scheme',
                    type='cube',
                    children=[dbc.Card(
            id='block_built_nucleus'
        ),])
    ]
)


app.title = 'Interactive Nuclear Chart'

header = html.Div(
    [
        dbc.Card(
            [
                html.H1('Welcome to the Interactive Nuclear Chart!'),
                html.Hr(),
                html.P('If you haven\'t already played our game, check it out here!')
            ]
        ),
    ]
)

tips = html.Div(
    [
        html.H4('Tips:',className='card-title'),
        dbc.ListGroup(
            [
                dbc.ListGroupItem(
                    'The chart starts with the maximum view setting of 20 protons and 28 neutrons.'+
                    ' Be sure to click the \"Nuclear Chart Options\" button to play around with the '+
                    'chart type and number of protons and neutrons viewed.'
                ),
                dbc.ListGroupItem(
                    'All of the nuclei on the nuclear chart have been acually observed by scientists!'+
                    ' That being said, we need your help to build (\"discover\") a block version of each one.'
                ),
                dbc.ListGroupItem(
                    'Click on a specific nucleus to see its level scheme on the left panel below and a '+
                    'picture of its ground state which was built by another user on the right below. It\'s '+
                    'possible that no one has managed to build that state or submitted their \"discovery\", '+
                    'so if that\'s the case consider submitting your own construction!'
                )
            ],
            numbered=True
        ),
        html.Br(),
        html.Div(
            [
                dbc.Button('Open Nuclear Chart Options',id='open_chart_offcanvas',n_clicks=0),
                chart_options,
            ]
        ),
    ]
)

primaryTab = html.Div([
    dbc.Card([
        dbc.Row([
            dbc.Card([
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                tips
                            ], width=3
                        ),
                        dbc.Col(
                            [
                                chart_plot
                            ], width=6
                        ),
                        dbc.Col([
                            level_scheme,
                            built_nucleus_images
                        ], width=3),
                    ]
                )
            ])
        ], align='center'), 
        # html.Br(),
        # dbc.Row([
        #     # dbc.Col([
        #     #     level_scheme
        #     # ], width=6),
        #     dbc.Col([
        #         built_nucleus_images
        #     ], width=6),
        # ], align='center'),      
    ])
])


submissionsTab = html.Div(
    [
        html.H1('Did you discover a new nucleus?'),
        html.Hr(),
        dbc.Card(
            [
                dbc.Row([
                    dbc.Col(
                        [
                            dbc.CardBody(
                                [
                                    html.Td([dcc.Link('Click here',href='https://forms.gle/wKGLPipALwGx9fuA6',target='_blank'),
                                             ' or scan the QR code to document your discovery and start the peer review process!']),
                                    html.Br(),
                                    html.Td(['Note: Peer-Reviewing takes time and is usually done by volunteers. This may lead to ',
                                             'a delay in the publication of your nuclear data.'])
                                ]
                            ),
                        ],width=4
                    ),
                    dbc.Col(
                        [
                            dbc.CardImg(src='assets/form_qr_code.png'),
                        ],width=4
                    )
                ])
            ],
        )
    ]
)



app.layout = html.Div([
    header,
    dbc.Tabs(
        [
            dbc.Tab(primaryTab, label='Interactive Chart'),
            dbc.Tab(submissionsTab, label='Discovery Submissions')
        ]
    )
])



# Plotting functions which will be used below
def plot_separation_energy(fig_,s_,nucType,nucColor):
    try: # When we don't have a separation energy, the conversion to float will throw an error
        s_ = float(s_) * 10**-3 # Convert to MeV
        full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
        xAxisRange = full_fig.layout.xaxis.range
        # print(xAxisRange)
        fig_.add_trace(go.Scatter(
            x=xAxisRange, y=[float(s_),float(s_)],
            mode='lines',
            hoverinfo='skip', # Don't provide any hover info or hover interaction from this line
            name=f'{nucType} Separation Energy',
            line=dict(color=nucColor,dash='dash'),
        ))
    except:
        # print('printing exception')
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

    full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
    xAxisRange = full_fig.layout.xaxis.range
    yAxisRange = full_fig.layout.yaxis.range
    fig_.update_xaxes(range=[min(xAxisRange)-0.25,max(xAxisRange)+0.25])
    fig_.update_yaxes(range=[min(yAxisRange)-0.1,max(yAxisRange)+0.1])

    sn = isotope['sn'].values[0] # Still in string format! Handle with function below...
    sp = isotope['sp'].values[0] # Still in string format! Handle with function below...
    plot_separation_energy(fig_,sn,'Neutron','blue')
    plot_separation_energy(fig_,sp,'Proton','red')
    fig_.update_legends()
    fig_.update_layout(legend=dict(orientation='h',
                                   yanchor="bottom",y=1.02,
                                   xanchor="right",x=1))
    fig_.update_xaxes(title_text='State',
                      ticktext=list(position_to_name.values()),
                      tickvals=list(position_to_name.keys()))
    fig_.update_yaxes(title_text='Energy (MeV)')
    return fig_, headerText_

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
        # xref="paper",
        # yref="paper",
        sizex=1,
        sizey=1,
        xanchor="center",
        yanchor="middle"
    ))



# Now set any necessary callbacks corresponding to the ids given in the layout section
@app.callback(
    Output("offcanvas", "is_open"),
    Input("open_chart_offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

@callback(
    Output('nuclear_chart','figure'),
    Input('chart_type','value'),
    Input('neutron_axis_slider','value'),
    Input('proton_axis_slider','value')
)
def update_chart_type(chart_type_name,neutron_slider,proton_slider):
    currentData = ground_state.loc[(ground_state['n']<=neutron_slider)&(ground_state['z']<=proton_slider),:].copy()
    xoffset, yoffset = 2, 2.5
    xrange = [min(currentData['n'])-xoffset, max(currentData['n'])]
    yrange = [min(currentData['z'])-yoffset, max(currentData['z'])]
    chart = go.Figure()

    if chart_type_name == 'Half Life':
        # Update colorbar in the following list
        custom_colors = [
            [0.0, 'rgb(143, 0, 255)'],  # Violet zeptosecond
            [0.05, 'rgb(0, 0, 255)'],  # Blue attosecond
            [0.267, 'rgb(0, 255, 0)'],  # Green microsecond
            [0.375, 'rgb(255, 255, 0)'],  # Yellow megasecond (12 days)
            [0.536, 'rgb(255, 165, 0)'],  # Orange
            [0.75, 'rgb(255, 0, 0)'],  # Red
            [0.95, 'rgb(0, 0, 0)'],  # Black
            [1.0, 'rgb(200, 200, 200)'],  # Grey
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
            dataDecay[row['z']][row['n']] = 'Not Available'

        # Recreate the map
        unstableNuclei = currentData[(currentData['half_life']!='STABLE')&(currentData['half_life']!=' ')]
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
                        ticktext=['zs','ns','s','Gs (or 31.7 years)','Zs (or 31.7 trillion years)','Stable (Black)','Unknown (Grey)']),
        )

        chart.add_traces([unstableMap])
    
    drawMagicNumbers(chart,xrange,yrange,xoffset, yoffset)
    # ADD IF STATEMENTS FOR OTHER CHART TYPES HERE AND BE SURE TO INCLUDE IT IN THE DROPDOWN MENU IN THE LAYOUT ABOVE
    # elif chart_type_name == 'Main Decay Mode':
    chart.update_layout(yaxis_scaleanchor='x',title=dict(text='Nuclear Chart: log(Half Life)')) # Fix aspect ratio
    chart.update_xaxes(title_text='Number of Neutrons',showspikes=True,range=xrange,showgrid=False)
    chart.update_yaxes(title_text='Number of Protons',showspikes=True,range=yrange,automargin=True,showgrid=False)
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
    # Output('display_level_nucleus_name','children'),
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
        levels.update_layout(title=dict(text=f'Please select a nucleus:')) # Title
    elif triggerID == 'nuclear_chart':
        levels, headerText = plot_level_scheme()

        # Get list of files in directory
        picturePath = 'assets/Approved_Pictures'
        directoryFiles = [f for f in os.listdir(picturePath) if os.path.isfile(os.path.join(picturePath,f))]
        # Get ground state file name given path, A, and symbol
        pictureFile = [f for f in directoryFiles if (str(A) + symbol + '_0') in f]
        # For showing picture of built nucleus
        if not pictureFile: # If picture file list is empty
            text = ['Hey, it looks like no one has discovered this state yet! Did you make this state?']#,html.Br(),
                    # 'Upload a picture of your nuclear discovery by clikcing on the \"Discovery Submissions\" tab above.']
            image = imagePath + 'nuclear_discovery_logo.png'
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,image)
        else:
            discovererNames = collaboratorNames(pictureFile[0])
            text = ['You\'re currently looking at the excited  of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames]
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,os.path.join(picturePath,pictureFile[0]))
        
        levels.update_layout(title=dict(text=f'Level Scheme for <sup>{A}</sup>{symbol}')) # Title

    elif triggerID == 'level_scheme':
        levels, headerText = plot_level_scheme()

        A = isotopeLevels['n'].unique()[0] + isotopeLevels['z'].unique()[0]
        symbol = isotopeLevels['symbol'].unique()[0]
        excitation = dumpHover['points'][0]['pointIndex']
        # Get list of files in directory
        picturePath = 'assets/Approved_Pictures'
        directoryFiles = [f for f in os.listdir(picturePath) if os.path.isfile(os.path.join(picturePath,f))]
        # Get ground state file name given path, A, and symbol
        pictureFile = [f for f in directoryFiles if (str(A) + symbol + f'_{int(excitation)}') in f]
        # For showing picture of built nucleus
        if not pictureFile:
            text = ['Hey, it looks like no one has discovered this state yet! Did you make this state?']#,html.Br(),
                    # 'Upload a picture of your nuclear discovery by clikcing on the \"Discovery Submissions\" tab above.']
            image = imagePath + 'nuclear_discovery_logo.png'
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,image)
        else:
            discovererNames = collaboratorNames(pictureFile[0])
            text = ['You\'re currently looking at the excited  of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames]
            builtNucleusHeader, builtNucleusPicture = show_built_nucleus(text,os.path.join(picturePath,pictureFile[0]))
        
        levels.update_layout(title=dict(text=f'Level Scheme for <sup>{A}</sup>{symbol}')) # Title
    
    # return levels, headerText, builtNucleusHeader, builtNucleusPicture
    return levels, builtNucleusHeader, builtNucleusPicture






# Run app...
if __name__ == '__main__':
    app.run(debug=True)