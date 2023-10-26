'''
This is the main code for the Nuclear Building Blocks site. It serves as the main Dash/Plotly base.

Written by:
 - Joshua Wylie
'''

# Import common packages
import pandas as pd
import numpy as np
import os

# Import Dash / Plotly Functions
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback, no_update
from dash import ctx # Used for identifying callback_context
import dash_daq as daq
import dash_bootstrap_components as dbc
import json

# Import helpful iaea nuclear data functions
import iaea_data as iaea

# Custom dash functions related to this code
import nuclear_chart_display_types as ncdt
import level_scheme_display_functions as lsdf

# Call ground state information from IAEA
ground_state = iaea.NuChartGS()
currentData = None # Initialize a global variable to cut down on the number of reloads required to look at a nucleus level scheme
# Call specific level scheme
isotopeLevels = None # Initialize a global variable to cut down on the number of reloads required to look at a nucleus level scheme

#%%
# Functions for this file only
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

def getExcitationGroupString(string_):
    # According to naming convention {A}{sym}_{exc}-{name1};{name2}.png, excitation is the middle part
    state = string_.split('-')[0] # Gives {A}{sym}_{exc}
    state = int(state.split('_')[-1]) # Gives {exc}
    exDict = {0:['ground',' ','state'], 1:[1,html.Sup('st'),' excited state'],
              2:[2,html.Sup('nd'),' excited state'], 3:[3,html.Sup('rd'),' excited state']}
    return exDict[state]


#%%
# Begin designing dash layout and components of layout
app = Dash(__name__,external_stylesheets=[dbc.themes.SLATE])
# app = Dash(__name__,meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])

######################################################################
########## Dash layout components relating to Nuclear Chart ##########
######################################################################
# Layout component of options within the offcanvas section (controlled by button on main page)
chart_options = dbc.Offcanvas(
    [
        ##### View Type #####
        dbc.Card(
            [
                dbc.Label('Please select your desired view:'),
                dcc.Dropdown(
                    ['Half Life', 'Binding Energy Per Nucleon', 'Year Discovered'],
                    'Half Life',
                    id='chart_type'
                )
            ]),
        ##### Proton Slider #####
        dbc.Card(
            [
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
        ##### Neutron Slider #####
        dbc.Card(
            [
                dbc.Label('Show Neutron Range:'),
                dcc.Slider(
                    ground_state['n'].min(),
                    ground_state['n'].max(),
                    step=None,
                    id='neutron_axis_slider',
                    # value=ground_state['n'].max()
                    value=28
                ),
            ],
        ),
        ##### Extra Clickable Options #####
        # Add code here...
        dbc.Card(
            [
                ##### Toggle Options #####
                dbc.Label('Toggle Options:'),
                dbc.Checklist(
                    options=[
                        {'label':'Show N=Z line','value':1},
                        {'label':'Show User-Made Nuclei','value':2}
                    ],
                    value=[2],
                    id='chart_toggle_options',
                    switch=True
                    # value=ground_state['n'].max()
                ),
                ##### Extra Toggle Options #####
                # Add code here...
            ],
        )
    ],
    id='offcanvas',
    is_open=False,
    title='Nuclear Chart Options'
)
# Layout component of plot of nuclear chart itself
chart_plot = dbc.Card(
    [
        ##### Nuclear Chart #####
        dcc.Graph(
            id='nuclear_chart',style={'height':'80vh'},
            clear_on_unhover=True
        ),
        dcc.Tooltip(id='chart_tooltip')
    ]
)

#####################################################################
########## Dash layout components relating to Level Scheme ##########
#####################################################################
level_scheme = dbc.Card(
    [
        ##### Level Scheme Plot #####
        dcc.Graph(
            id='level_scheme',style={'height':'45vh'}
        ),
    ]
)
built_nucleus_images = dbc.Card(
    [
        dbc.Label(id='display_built_nucleus_name'), # Lable for user built nuclei
        ##### Load Images of User-Built Nuclei #####
        dcc.Loading(id='loading_level_scheme',
                    type='cube',
                    children=[dbc.Card(
            id='block_built_nucleus'
        ),])
    ]
)


##############################################################################
########## Dash layout components relating to overall app structure ##########
##############################################################################
header = html.Div(
    [
        ##### Information in App Header #####
        dbc.Card(
            [
                html.H1('Welcome to the Interactive Nuclear Chart!'),
                html.Hr(),
                html.P('If you haven\'t already played our game, check it out here!'),
                # Add code here...
            ]
        ),
    ]
)

tips = html.Div(
    [
        ##### Information in "Tips" section #####
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
                ),
                # Add code for more Tips here...
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
        # Add code for more buttons or other options here...
    ]
)

#########################################################
########## Dash layout structure for first tab ##########
#########################################################
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
    ])
])

##########################################################
########## Dash layout structure for second tab ##########
##########################################################
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

################################################################
########## Begin defining actual Dash app information ##########
################################################################
app.title = 'Interactive Nuclear Chart'

app.layout = html.Div([
    header,
    dbc.Tabs(
        [
            dbc.Tab(primaryTab, label='Interactive Chart'),
            dbc.Tab(submissionsTab, label='Discovery Submissions')
            # Add additional tabs here...
        ]
    )
])


######################################################################
########## Callbacks for interactive figures, options, etc. ##########
######################################################################

##### Offcanvas options callbacks #####
@app.callback(
    Output("offcanvas", "is_open"),
    Input("open_chart_offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open

##### Nuclear Chart callbacks #####
@callback(
    Output('nuclear_chart','figure'),
    Input('chart_type','value'),
    Input('neutron_axis_slider','value'),
    Input('proton_axis_slider','value'),
    Input('chart_toggle_options','value')
)
def update_chart_type(chart_type_name,neutron_slider,proton_slider,toggle_options):
    global currentData # Use global data to allow other functions easy access. Might need to change later...
    # Filter current data to the slider callbacks
    currentData = ground_state.loc[(ground_state['n']<=neutron_slider)&(ground_state['z']<=proton_slider),:]

    # Additional axes offsets to show magic number tiles later
    xoffset, yoffset = 2, 2.5
    xrange = [min(currentData['n'])-xoffset, max(currentData['n'])+0.5]
    yrange = [min(currentData['z'])-yoffset, max(currentData['z'])]
    chart = go.Figure()

    ##### If statements for each chart_type_name callback option #####
    if chart_type_name == 'Half Life':
        chart_type = ncdt.half_life_plot(currentData)
        chart.add_traces([chart_type])
        chart.update_layout(title=dict(text='Nuclear Chart: log(Half Life)'))
        
    elif chart_type_name == 'Binding Energy Per Nucleon':
        chart_type = ncdt.binding_energy_per_nucleon_plot(currentData)
        chart.add_traces([chart_type])
        chart.update_layout(title=dict(text='Nuclear Chart: Binding Energy Per Nucleon'))
    
    elif chart_type_name == 'Year Discovered':
        chart_type = ncdt.year_discovered_plot(currentData)
        chart.add_traces([chart_type])
        chart.update_layout(title=dict(text='Nuclear Chart: Year Discovered'))

    # Draw magic numbers
    ncdt.drawMagicNumbers(chart,xrange,yrange,xoffset, yoffset)

    # Set any chart labels, aspect ratio, etc.
    chart.update_layout(yaxis_scaleanchor='x') # Fix aspect ratio
    chart.update_xaxes(title_text='Number of Neutrons',showspikes=True,range=xrange,showgrid=False)
    chart.update_yaxes(title_text='Number of Protons',showspikes=True,range=yrange,automargin=True,showgrid=False)
    
    # Suppress Plotly default hover info and replace later with 'display_hover' function
    chart.update_traces(hoverinfo='none',hovertemplate=None)
    
    ##### Toggle Options from Offcanvas callbacks #####
    if 1 in toggle_options:
        # Find which is larger to set our line boundaries
        points = [min(currentData['n']), max(currentData['n'])]
        if (points[0] >= min(currentData['z'])) and (points[1] > max(currentData['z'])):
            points = [min(currentData['z']), max(currentData['z'])]
        chart.add_trace(go.Scatter(
            x=points,
            y=points,
            mode="lines",
            name='N=Z Line',
            showlegend=False
        ))
    if 2 in toggle_options:
        ncdt.show_user_made_nuclei(chart,currentData)
    return chart

##### More sophisticated hovermode for Nuclear Chart controlled through the following callback #####
@callback(
    Output("chart_tooltip", "show"),
    Output("chart_tooltip", "bbox"),
    Output("chart_tooltip", "children"),
    Input("nuclear_chart", "hoverData"),
)
def display_hover(hoverData):
    global currentData
    if hoverData is None:
        return False, no_update, no_update

    # demo only shows the first point, but other points may also be available
    pt = hoverData["points"][0]
    bbox = pt["bbox"]

    # Get data for current hover item
    df_row = currentData[(currentData['n']==pt['x'])&(currentData['z']==pt['y'])]
    # For no data, Return nothing
    if df_row.empty:
        return False, no_update, no_update
    
    # Dictionary of possible decay mode image paths
    decayImgSrc = {
        'B-':'assets/decay_modes/beta-.png',
        'B+':'assets/decay_modes/beta+.png',
        'EC':'assets/decay_modes/EC.png',
        'N':'assets/decay_modes/N.png',
        'P':'assets/decay_modes/P.png',
        '2N':'assets/decay_modes/2N.png',
        '2P':'assets/decay_modes/2P.png',
        'A':'assets/decay_modes/A.png',
        'nan':'assets/decay_modes/unknown.png',
        'Stable':'assets/decay_modes/stable.png',
    }
    # Dictionary of shown information on hover for the decay mode
    decayName = {
        'B-':['Decays by: \u03B2',html.Sup('-'),' Decay'],
        'B+':['Decays by: \u03B2',html.Sup('+'),' Decay'],
        'EC':'Decays by: Electron Capture',
        'N':'Decays by: Neutron Emission',
        'P':'Decays by: Proton Emission',
        '2N':'Decays by: 2 Neutron Emission',
        '2P':'Decays by: 2 Proton Emission',
        'A':['Decays by: \u03B1 Decay'],
        'nan':'Unknown Decay Mode',
        'Stable':'Stable'
    }

    img_src = decayImgSrc[str(df_row['common_decays'].values[0])] # Get decay image location
    A =  int(df_row['n'].values[0])+int(df_row['z'].values[0]) # Get A value
    symbol = df_row['symbol'].values[0] # Get element symbol
    text = [html.Sup(str(A)), symbol] # Compile Isotope name into correct scientific format with superscript

    # If a user has made at least one state of this nucleus, display the 'User discovered' note
    if ncdt.check_if_user_made(A,symbol):
        discovered = [html.Sub('User Discovered')]
    else:
        discovered = []

    # Describe layout of hover info as a html.Div()
    children = [
        html.Div([
            dbc.Row(
                [
                    dbc.Col(
                        html.H1(text), # Header with Isotope name
                    ),
                    dbc.Col(
                        html.P(discovered) # Display if discovered
                    )
                ]
            ),
            html.P(decayName[str(df_row['common_decays'].values[0])]), # Decay mode type name
            html.Img(src=img_src, style={"width": "100%"}), # Decay mode type image
            # Add extra code here for more details for each nucleus...
            html.P(['Images are a general depiction of the decay process.' +
                    ' They may only show an example nucleus in the decay, not the current viewed nucleus'],
                   style={'font-size':'12px'}), # Tiny disclaimer at the bottom
        ], style={'width': '200px', 'white-space': 'normal'})
    ]

    return True, bbox, children


##### Level Scheme callbacks #####
@callback(
    Output('level_scheme','figure'),
    Output('display_built_nucleus_name','children'),
    Output('block_built_nucleus','children'),
    Input('nuclear_chart','clickData'),
    Input('level_scheme','hoverData')
)
def update_level_scheme(clickData, hoverData):
    global isotopeLevels # Modify global variable of isotope levels
    dumpClick = json.loads(json.dumps(clickData)) # json info from clicking nuclear chart
    dumpHover = json.loads(json.dumps(hoverData)) # json info from hovering over level scheme levels or group
    triggerID = ctx.triggered_id # Determine the type of id that was triggered (hover, click, or None)

    # When we click on a new nucleus on the nuclear chart, load the corresponding level data, this avoids unnecessary reloads
    if triggerID == 'nuclear_chart':
        nucChartDump = dumpClick['points'][0] 
        n, z = nucChartDump['x'], nucChartDump['y']
        element = ground_state.loc[(ground_state['z']==z)] # Get element chain data
        isotope = element[element['n']==n] # Get specific isotope data
        symbol = isotope['symbol'].values[0] # Get corresponding symbol name for element
        A = n + z
        
        # Get level data and plot levels
        isotopeLevels = iaea.NuChartLevels(A,symbol)
    
    imagePath = 'assets/'
    # Default don't show a level scheme
    if triggerID is None:
        ### Level scheme ###
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

        ### Built nucleus image ###
        # Default header information 
        text = ['Please select a nucleus to see a block version of it: ']
        image = imagePath + 'logo.png'
        builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,image) # Shows default logo and text
        levels.update_layout(title=dict(text=f'Please select a nucleus:')) # Title

    # When a nucleus is selected on the nuclear chart, update level scheme and image to ground state '_0'
    elif triggerID == 'nuclear_chart':
        ### Level scheme ###
        # Note, we can also print the detailed level scheme for each level using function plot_level_scheme()
        levels = lsdf.plot_simplified_level_scheme(ground_state,isotopeLevels)
        levels.update_layout(title=dict(text=f'Level Scheme for <sup>{A}</sup>{symbol}')) # Title

        ### Built nucleus image ###
        # Get list of files in desired directory (note: all images MUST be in a directory called 'assets')
        picturePath = 'assets/Approved_Pictures'
        directoryFiles = [f for f in os.listdir(picturePath) if os.path.isfile(os.path.join(picturePath,f))]
        # Get ground state file name given path, A, and symbol
        pictureFile = [f for f in directoryFiles if (str(A) + symbol + '_0') in f]

        # For showing picture of built nucleus
        if not pictureFile: # If picture file list is empty, display discovery image and text
            text = ['Hey, it looks like no one has discovered this state yet! Did you make this state?']
            image = imagePath + 'nuclear_discovery_logo.png'
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,image)
        else: # If picture was found, shows the ground state
            discovererNames = collaboratorNames(pictureFile[0])
            text = ['You\'re currently looking at the ground state of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames]
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,os.path.join(picturePath,pictureFile[0]))

    # When a level or excitation group is hovered over on the level scheme graph, update built image to the excitation '_#'
    elif triggerID == 'level_scheme':
        # Get data for level or excitation group before displaying image or level scheme
        A = isotopeLevels['n'].unique()[0] + isotopeLevels['z'].unique()[0]
        symbol = isotopeLevels['symbol'].unique()[0]
        # excitation = dumpHover['points'][0]['pointIndex'] # old usage for plot_level_scheme() function
        excitation = dumpHover['points'][0]['customdata'][0] # new usage for plot_simplified_level_scheme() function

        ### Level scheme ###
        # Note, we can also print the detailed level scheme for each level using function plot_level_scheme()
        levels = lsdf.plot_simplified_level_scheme(ground_state,isotopeLevels)
        levels.update_layout(title=dict(text=f'Level Scheme for <sup>{A}</sup>{symbol}')) # Title

        ### Built nucleus image ###
        # Get list of files in directory
        picturePath = 'assets/Approved_Pictures'
        directoryFiles = [f for f in os.listdir(picturePath) if os.path.isfile(os.path.join(picturePath,f))]
        # Get ground state file name given path, A, and symbol
        pictureFile = [f for f in directoryFiles if (str(A) + symbol + f'_{int(excitation)}') in f]

        # For showing picture of built nucleus
        if not pictureFile: # If picture file list is empty, display discovery image and text
            text = ['Hey, it looks like no one has discovered this state yet! Did you make this state?']
            image = imagePath + 'nuclear_discovery_logo.png'
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,image)
        else: # If picture was found, shows the ground state
            discovererNames = collaboratorNames(pictureFile[0]) # Given a file name, get a string of collaborator names
            exString = getExcitationGroupString(pictureFile[0]) # Given a file name, get the excitation in a nice html format
            text = [f'You\'re currently looking at the ', exString[0], exString[1], exString[2], ' of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames]
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,os.path.join(picturePath,pictureFile[0]))
    
    return levels, builtNucleusHeader, builtNucleusPicture






# Run app...
if __name__ == '__main__':
    app.run(debug=True)