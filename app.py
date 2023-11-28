'''
This is the main code for the Nuclear Building Blocks site. It serves as the main Dash/Plotly base.

Written by:
 - Joshua Wylie
'''

# Import common packages
import pandas as pd
from io import StringIO # For handling new json format in pandas
import numpy as np
import os
import tempfile # For saving as svg

# Import Dash / Plotly Functions
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback, no_update
from dash import ctx # Used for identifying callback_context
import dash_bootstrap_components as dbc
# from dash_extensions.snippets import send_data_frame
import json
# from dash_breakpoints import WindowBreakpoints

# Import helpful iaea nuclear data functions
import iaea_data as iaea

# Custom dash functions related to this code
import nuclear_chart_display_types as ncdt
import level_scheme_display_functions as lsdf
import hover_nuclear_data as hnd

# Uncomment to see layout properties of chosen theme above to set text, background, etc. 
from dash_bootstrap_templates import load_figure_template
import plotly.io as pio

# Call ground state information from IAEA
# ground_state = iaea.NuChartGS() # Since it's a universal dataset which is not modified, it's okay to leave here

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

theme = dbc.themes.CYBORG
theme_name = 'cyborg'

load_figure_template(theme_name)
plotly_template = pio.templates[theme_name]
plotly_template.layout = {
    'xaxis': {
        'titlefont': {
            'color': 'white',  # Set to a color that's visible on the dark background
            'size': 16,
        },
        'tickfont': {
            'color': 'white',  # Set to a suitable color
            'size': 12,
        },
    },
    'yaxis': {
        'titlefont': {
            'color': 'white',  # Set to a color that's visible on the dark background
            'size': 16,
        },
        'tickfont': {
            'color': 'white',  # Set to a suitable color
            'size': 12,
        },
    },
    'legend': {
        'font': {
            'color': 'white'
        }
    },
    'paper_bgcolor': '#292b2c',  # Set the background color to match CYBORG theme
    'plot_bgcolor': '#292b2c',  # Set the background color to match CYBORG theme
}
# write to file for easy viewing
# with open('layout_plotly_template.txt', 'w') as file:
#     for item in plotly_template.layout:
#         file.write(item+': ')
#         file.write(str(plotly_template.layout[item])+'\n')

app = Dash(__name__,external_stylesheets=[theme])
server = app.server
app.title = 'Interactive Nuclear Chart'

##########################################################################################
#################### Subcomponents of Layout are presented first here ####################
##################### See next section for overall Layout structure ######################
##########################################################################################

######################################################################
############################## Header ################################
######################################################################
header = html.Div(
    [
        ##### Information in App Header #####
        dbc.Card(
            [
                html.H1('Welcome to the Interactive Nuclear Chart!'),
                html.Hr(),
                html.H5('If you haven\'t already played our game, check it out here!'),
                # Add code here...
            ]
        ),
    ]
)

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
                    ['Half Life', 'Decay Mode', 'Binding Energy Per Nucleon', 'Year Discovered'],
                    'Decay Mode',
                    id='chart_type',
                    clearable=False,
                )
            ]),
        ##### Proton Slider #####
        dbc.Card(
            [
                dbc.Label('Show Proton Range:'),
                dcc.Slider(
                    # min=ground_state['z'].min(),
                    # max=ground_state['z'].max(),
                    min=0,
                    max=118,
                    step=None,
                    id='proton_axis_slider',
                    # value=ground_state['z'].max()
                    value=20
                )
            ]),
        ##### Neutron Slider #####
        dbc.Card(
            [
                dbc.Label('Show Neutron Range:'),
                dcc.Slider(
                    # min=ground_state['n'].min(),
                    # max=ground_state['n'].max(),
                    min=0,
                    max=178,
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
        ),
        dbc.Card(
            [
                ##### Export Options #####
                dbc.Label('Click to export chart as:'),
                html.Button("svg", id="btn_svg_download"),
                dcc.Download(id="download-image"),
                ##### Extra Export Options #####
                # Add code here...
            ],
        ),
    ],
    id='offcanvas',
    is_open=False,
    title='Nuclear Chart Options',
)
# Layout component of plot of nuclear chart itself
chart_plot = dbc.Card(
    [
        ##### Nuclear Chart #####title = 'Nuclear Chart: log(Half Life)'
        dbc.CardHeader(id='nuclear_chart_title'),
        dcc.Graph(
            id='nuclear_chart',
            clear_on_unhover=True,
            style={'height':'80vh'},
        ),
        dcc.Tooltip(id='chart_tooltip',
                    background_color=None,
                    border_color=None)
    ], className='nuclear_chart', #color='dark'
)

######################################################################
############################## Tips ##################################
######################################################################
tips = html.Div(
    [
        ##### Information in "Tips" section #####
        dbc.Card(
            [
                # html.H4('Tips:'),
                dbc.CardHeader([html.H4('Tips:'),]),
                dbc.ListGroup(
                    [
                        dbc.ListGroupItem(
                            'The chart starts with the maximum view setting of 20 protons and 28 neutrons.'+
                            ' Be sure to click the \"Nuclear Chart Options\" button to play around with the '+
                            'chart type and number of protons and neutrons viewed.',
                            color='secondary',
                        ),
                        dbc.ListGroupItem(
                            'All of the nuclei on the nuclear chart have been acually observed by scientists!'+
                            ' That being said, we need your help to build (\"discover\") a block version of each one.',
                            color='secondary',
                        ),
                        dbc.ListGroupItem(
                            'Click on a specific nucleus to see its level scheme on the left panel below and a '+
                            'picture of its ground state which was built by another user on the right below. It\'s '+
                            'possible that no one has managed to build that state or submitted their \"discovery\", '+
                            'so if that\'s the case consider submitting your own construction!',
                            color='secondary',
                        ),
                        # Add code for more Tips here...
                    ],
                    numbered=True,
                ),
                html.Br(),
                html.Div(
                    [
                        dbc.Button('Open Nuclear Chart Options',id='open_chart_offcanvas',n_clicks=0),
                        chart_options,
                    ]
                ),
                # Add code for more buttons or other options here...
            ],color='secondary'
        )
    ], className='tips',
)

#####################################################################
########## Dash layout components relating to Level Scheme ##########
#####################################################################
levels = html.Div(
    [
        ##### Level Scheme Plot #####
        dbc.Card(
            [
                dbc.CardHeader(id='level_scheme_title'),
                dcc.Graph(
                    id='level_scheme',#,style={'height':'50vh'}
                ),
            ], #color='dark'
        ),
    ], className='images',
)
nucleus_images = html.Div(
    [
        ##### Load Images of User-Built Nuclei #####
        dcc.Loading(id='loading_level_scheme',
                    type='cube',
                    children=[dbc.Card(
                        [
                            dbc.CardHeader(id='built_nucleus_title'),
                            dbc.CardImg(id='built_nucleus')
                        ], #color='dark'
                    )]
        )
    ], className='levels',
)
levels_and_nucleus_images = html.Div(
    [
        levels,
        nucleus_images,
    ], className='levels_and_images',
)


##########################################################################################
################ Dash layout components relating to overall app structure ################
##########################################################################################
#########################################################
########## Dash layout structure for first tab ##########
#########################################################
primaryTab = html.Div([
    tips,
    chart_plot,
    levels_and_nucleus_images,
],className='primary_container')

##########################################################
########## Dash layout structure for second tab ##########
##########################################################
submissionsTab = html.Div(
    [
        html.H3('Did you discover a new nucleus?'),
        html.Hr(),
        html.Div(
            [
                dbc.Card(
                    [
                        dbc.CardBody(html.H5([dcc.Link('Click here',href='https://forms.gle/wKGLPipALwGx9fuA6',target='_blank'),
                                    ' or scan the QR code to document your discovery and start the peer review process!'])),
                        dbc.CardImg(src='assets/form_qr_code.png',bottom=True),
                    ], className='submission_links',
                ),
                dbc.Card(
                    [
                        dbc.CardHeader([html.H4('Note:')]),
                        dbc.CardBody(
                            [
                                dbc.ListGroup(
                                    [
                                        dbc.ListGroupItem(
                                            'Peer-Reviewing takes time and is usually done by volunteers. This may lead to '+
                                            'a delay in the publication of your nuclear data.'
                                        ),
                                        dbc.ListGroupItem(
                                            'We do not require the submission of any personal information in the submission of '+
                                            'pictures for peer-review.'
                                        ),
                                        dbc.ListGroupItem(
                                            ['Minors (anyone under the age of 18) ',
                                            html.B('must obtain approval from their parent or guardian'),
                                            ' before submitting any information into the peer-review process to ensure their privacy.']
                                        ),
                                        # Add code for more Tips here...
                                    ],
                                ),
                            ]
                        )
                    ], className='submission_notes',
                ),
            ],className='secondary_container'
        )
    ]
)

################################################################
########## Begin defining actual Dash app information ##########
################################################################

app.layout = html.Div([
    header,
    html.Div(
        [
            html.Button(id='load_ground_state_data',style=dict(display='none')),
        ]
    ),
    dbc.Tabs(
        [
            dbc.Tab(primaryTab, label='Interactive Chart'),
            dbc.Tab(submissionsTab, label='Discovery Submissions')
            # Add additional tabs here...
        ]
    ),
    dcc.Store(id='ground_state'),
    dcc.Store(id='current_data'),
    dcc.Store(id='isotope_levels'),
    html.Link(rel="stylesheet", href="layout_styles.css")
])


######################################################################
########## Callbacks for interactive figures, options, etc. ##########
######################################################################

##### Initial ground state data callback #####
# Since all callbacks run on initialization, this should run only once
@callback(
    Output('ground_state','data'),
    Input("load_ground_state_data", "n_clicks"),
)
def update_chart_data(n_clicks):
    if n_clicks == None:
        # print('Running call to get ground state data...')
        # Call ground state information from IAEA
        ground_state = iaea.NuChartGS()
        # print(ground_state)
        return ground_state.to_json(orient='split')
    
    return no_update

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
# Selecting a subset of data
@callback(
    Output('current_data','data'),
    Input('neutron_axis_slider','value'),
    Input('proton_axis_slider','value'),
    Input('ground_state','data'),
)
def update_chart_data(neutron_slider,proton_slider,jsonGroundState):
    ground_state = pd.read_json(StringIO(jsonGroundState),orient='split')
    # Filter current data to the slider callbacks
    currentData = ground_state.loc[(ground_state['n']<=neutron_slider)&(ground_state['z']<=proton_slider),:]

    return currentData.to_json(orient='split')

# Selecting Toggles and other chart modifications
@callback(
    Output('nuclear_chart','figure'),
    Output('nuclear_chart_title','children'),
    Input('chart_type','value'),
    Input('current_data','data'),
    Input('chart_toggle_options','value')
)
def update_chart_type(chart_type_name,jsonCurrentData,toggle_options):
    currentData = pd.read_json(StringIO(jsonCurrentData),orient='split')
    # Additional axes offsets to show magic number tiles later
    xoffset, yoffset = 2, 2.5
    xrange = [min(currentData['n'])-xoffset, max(currentData['n'])+0.5]
    yrange = [min(currentData['z'])-yoffset, max(currentData['z'])]
    chart = go.Figure()

    ##### If statements for each chart_type_name callback option #####
    if chart_type_name == 'Half Life':
        chart_type = ncdt.half_life_plot(currentData)
        chart.add_traces([chart_type])
        # chart.update_layout(title=dict(text='Nuclear Chart: log(Half Life)'))
        title = html.H5(['Nuclear Chart: log(Half Life)'])
        
    if chart_type_name == 'Decay Mode':
        chart_type = ncdt.decay_mode_plot(currentData)
        chart.add_traces([chart_type])
        # chart.update_layout(title=dict(text='Nuclear Chart: log(Half Life)'))
        title = html.H5(['Nuclear Chart: Known Primary Decay Mode'])

    elif chart_type_name == 'Binding Energy Per Nucleon':
        chart_type = ncdt.binding_energy_per_nucleon_plot(currentData)
        chart.add_traces([chart_type])
        # chart.update_layout(title=dict(text='Nuclear Chart: Binding Energy Per Nucleon'))
        title = html.H5(['Nuclear Chart: Binding Energy Per Nucleon'])
    
    elif chart_type_name == 'Year Discovered':
        chart_type = ncdt.year_discovered_plot(currentData)
        chart.add_traces([chart_type])
        # chart.update_layout(title=dict(text='Nuclear Chart: Year Discovered'))
        title = html.H5(['Nuclear Chart: Year Discovered'])

    # Draw magic numbers
    ncdt.drawMagicNumbers(chart,xrange,yrange,xoffset, yoffset)

    # Set any chart labels, aspect ratio, etc.
    magicNumbers = [2, 8, 20, 28, 50, 82, 126]
    # store current values of magic numbers that fall within given range
    xVals = [m for m in magicNumbers if (m >= min(xrange)) and (m <= max(xrange))]
    yVals = [m for m in magicNumbers if (m >= min(yrange)) and (m <= max(yrange))]
    chart.update_layout(yaxis_scaleanchor='x') # Fix aspect ratio
    chart.update_xaxes(title_text='Number of Neutrons',showspikes=True,range=xrange,showgrid=False,side='top',tickvals=xVals)
    chart.update_yaxes(title_text='Number of Protons',showspikes=True,range=yrange,automargin=True,showgrid=False,tickvals=yVals)
    
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
            hoverinfo='skip',
            line=dict(color='#5eb588',width=5),
            showlegend=False
        ))
    if 2 in toggle_options:
        ncdt.show_user_made_nuclei(chart,currentData)
        
    return chart, title

##### Download chart image #####
# Callback to handle SVG download
@app.callback(
    Output("download-image", "data"),
    Input("btn_svg_download", "n_clicks"),
    Input('nuclear_chart','figure'),
)
def download_svg(n_clicks, chart):
    if n_clicks is None:
        return None

    # Convert Plotly figure to SVG
    svg_content = go.Figure(chart).to_image(format="svg", width=1200, height=800)

    # Create a temporary file to store the SVG content
    _, temp_filepath = tempfile.mkstemp(suffix=".svg")

    try:
        with open(temp_filepath, "wb") as f:
            f.write(svg_content)

        # Return the temporary file path for download
        return dcc.send_file(temp_filepath, "heatmap.svg")

    finally:
        # Clean up the temporary file after it's been sent for download
        os.remove(temp_filepath)

##### More sophisticated hovermode for Nuclear Chart controlled through the following callback #####
# for the sake of run performance, we've removed hover in place of click action to cut CPU usage
@callback(
    Output("chart_tooltip", "show"), # Returns 'show' property specifically used in dcc.Tooltip()
    Output("chart_tooltip", "bbox"), # Returns 'bbox' property specifically used in dcc.Tooltip()
    Output("chart_tooltip", "children"), # Returns 'children' property specifically used in dcc.Tooltip()
    Output("chart_tooltip", "direction"), # Returns 'direction' property specifically used in dcc.Tooltip()
    # Input("nuclear_chart", "hoverData"),
    Input("nuclear_chart", "clickData"),
    Input('neutron_axis_slider','value'),
    Input('current_data','data'),
)
# def display_hover(hoverData,neutron_slider,jsonCurrentData):
def display_hover(clickData,neutron_slider,jsonCurrentData):
    # global currentData
    if clickData is None:
        return False, no_update, no_update, no_update

    # demo only shows the first point, but other points may also be available
    pt = clickData["points"][0]
    bbox = pt["bbox"]

    # print('neutron_slider = ',neutron_slider)
    # print('hoverData = ',hoverData)
    # print('pt = \n',pt)
    # print('bbox = \n',bbox)

    # Get data for current hover item
    currentData = pd.read_json(StringIO(jsonCurrentData),orient='split')
    df_row = currentData[(currentData['n']==pt['x'])&(currentData['z']==pt['y'])]
    # For no data, Return nothing
    if df_row.empty:
        return False, no_update, no_update, no_update
    
    # print('df_row = ',df_row)

    img_src = hnd.decayImgSrc[str(df_row['common_decays'].values[0])] # Get decay image location
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
        dbc.Card([
            dbc.CardHeader(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                html.H1(text), # Header with Isotope name
                            ),
                            dbc.Col(
                                [
                                    html.P([hnd.symbol_elements[symbol]]),
                                    html.P(discovered,) # Display if discovered
                                ]
                            )
                        ]
                    ),
                ]
            ),
            html.P(hnd.decayName[str(df_row['common_decays'].values[0])]), # Decay mode type name
            html.Img(src=img_src, style={"width": "100%"}), # Decay mode type image
            # Add extra code here for more details for each nucleus...
            html.P(['Images are a general depiction of the decay process.' +
                    ' They may only show an example nucleus in the decay, not the current viewed nucleus'],
                   style={'font-size':'12px'}), # Tiny disclaimer at the bottom
        ],style={'width': '300px', 'white-space': 'normal'},color='secondary', inverse=True)
    ]

    # # To avoid being cutoff by the edge of the chart, move the direction the hover box appears
    direction = 'right'
    # midPt = min(neutron_slider) + (max(neutron_slider) - min(neutron_slider)) / 2
    midPt = neutron_slider / 2
    if pt['x'] > midPt:
        direction = 'left'
    return True, bbox, children, direction


##### Level Scheme callbacks #####
@callback(
    Output('level_scheme','figure'),            # Constructed graph sent to level_scheme layout element
    Output('level_scheme_title','children'),    # Constructed title children div layout element
    Output('built_nucleus','src'),              # Constructed graph sent to built_nucleus layout element
    Output('built_nucleus_title','children'),   # Constructed title children div layout element
    Output('isotope_levels','data'),            # Store isotope levels as json data for current user session
    Input('nuclear_chart','clickData'),         # Input data of selected nucleus from click on nuclear chart
    Input('level_scheme','clickData'),          # Input data of selected level from click on level scheme
    Input('isotope_levels','data'),             # Input json data of current list of levels (None if no isotope selected)
    Input('current_data','data'),               # Current data subset of ground state data from nuclear chart
)
def update_level_scheme(chartClickData, levelClickData, jsonIsotopeLevels,jsonCurrentData):
    '''
    This callback controls the level scheme and which built nuclei to display.

    1) We start by getting all the other input callback data
    2) We check if this is on initialization (all callback input data is None) and display defaults
    3) We check if callback was triggered by nuclear_chart -> which updates the built nuclear state considered and its levels
    4) We check if callback was triggered by level_scheme -> which updates only the built nuclear state
    '''
    # global isotopeLevels # Modify global variable of isotope levels
    dumpClick = json.loads(json.dumps(chartClickData)) # json info from clicking nuclear chart
    dumpHover = json.loads(json.dumps(levelClickData)) # json info from hovering over level scheme levels or group
    triggerID = ctx.triggered_id # Determine the type of id that was triggered (hover, click, or None)

    # print('triggerID = ',triggerID)
    # print('dumpClick = \n',dumpClick)
    # print('dumpHover = \n',dumpHover)
    # print('jsonIsotopeLevels = \n',jsonIsotopeLevels)
    # print('jsonCurrentData = \n',jsonCurrentData)

    imagePath = 'assets/'
    # Default don't show a level scheme
    if triggerID == 'current_data':
        ### Level scheme ###
        levels = go.Figure()
        levels.add_trace(go.Scatter(
            x=[1],
            y=[1],
            text=[lsdf.customwrap("Please click a nucleus to see its levels")],
            mode="text",
            hoverinfo='skip',
            textfont={
                'color':'white'
            }
        ))
        levels.update_yaxes(showticklabels=False,showgrid=False)
        levels.update_xaxes(showticklabels=False,showgrid=False)
        levels_title = html.H6(['Please select a nucleus:'])

        ### Built nucleus image ###
        # Default header information 
        text = html.H6(['Please select a nucleus to see a block version of it:'])
        image = imagePath + 'logo.png'
        return levels, levels_title, image, text, no_update

    # In the case someone clicks on an invalid nucleus on the nuclear chart, we don't send any updates
    if (triggerID == 'nuclear_chart') and (dumpClick['points'][0]['z'] == None):
        return no_update, no_update, no_update, no_update, no_update
    
    currentData = pd.read_json(StringIO(jsonCurrentData),orient='split')

    # When we click on a new nucleus on the nuclear chart, load the corresponding level data, this avoids unnecessary reloads
    if triggerID == 'nuclear_chart':
        nucChartDump = dumpClick['points'][0] 
        n, z = nucChartDump['x'], nucChartDump['y']
        element = currentData.loc[(currentData['z']==z)] # Get element chain data
        isotope = element[element['n']==n] # Get specific isotope data
        symbol = isotope['symbol'].values[0] # Get corresponding symbol name for element
        A = n + z
        
        # Get level data and plot levels
        isotopeLevels = iaea.NuChartLevels(A,symbol)
    else:
        isotopeLevels = pd.read_json(StringIO(jsonIsotopeLevels),orient='split')
    
    #### Loading Images of Built nuclei ####
    # When a nucleus is selected on the nuclear chart, update level scheme and image to ground state '_0'
    if triggerID == 'nuclear_chart':
        ### Level scheme ###
        # Note, we can also print the detailed level scheme for each level using function plot_level_scheme()
        levels = lsdf.plot_simplified_level_scheme(currentData,isotopeLevels)
        levels_title = html.H6(['Level Scheme for ',html.Sup(A),symbol])

        ### Built nucleus image ###
        # Get list of files in desired directory (note: all images MUST be in a directory called 'assets')
        picturePath = 'assets/Approved_Pictures'
        directoryFiles = [f for f in os.listdir(picturePath) if os.path.isfile(os.path.join(picturePath,f))]
        # Get ground state file name given path, A, and symbol
        pictureFile = [f for f in directoryFiles if (str(A) + symbol + '_0') in f]

        # For showing picture of built nucleus
        if not pictureFile: # If picture file list is empty, display discovery image and text
            text = html.H6(['Hey, it looks like no one has discovered this state yet! Did you make this state?'])
            image = imagePath + 'nuclear_discovery_logo.png'
        else: # If picture was found, shows the ground state
            discovererNames = collaboratorNames(pictureFile[0])
            text = html.H6(['You\'re currently looking at the ground state of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames])
            image = os.path.join(picturePath,pictureFile[0])

    # When a level or excitation group is hovered over on the level scheme graph, update built image to the excitation '_#'
    elif triggerID == 'level_scheme':
        # Get data for level or excitation group before displaying image or level scheme
        A = isotopeLevels['n'].unique()[0] + isotopeLevels['z'].unique()[0]
        symbol = isotopeLevels['symbol'].unique()[0]
        excitation = dumpHover['points'][0]['customdata'][0] # new usage for plot_simplified_level_scheme() function

        ### Level scheme ###
        # Note, we can also print the detailed level scheme for each level using function plot_level_scheme()
        levels = lsdf.plot_simplified_level_scheme(currentData,isotopeLevels)
        levels_title = html.H6(['Level Scheme for ',html.Sup(A),symbol])

        ### Built nucleus image ###
        # Get list of files in directory
        picturePath = 'assets/Approved_Pictures'
        directoryFiles = [f for f in os.listdir(picturePath) if os.path.isfile(os.path.join(picturePath,f))]
        # Get ground state file name given path, A, and symbol
        pictureFile = [f for f in directoryFiles if (str(A) + symbol + f'_{int(excitation)}') in f]

        # For showing picture of built nucleus
        if not pictureFile: # If picture file list is empty, display discovery image and text
            text = html.H6(['Hey, it looks like no one has discovered this state yet! Did you make this state?'])
            image = imagePath + 'nuclear_discovery_logo.png'
        else: # If picture was found, shows the ground state
            discovererNames = collaboratorNames(pictureFile[0]) # Given a file name, get a string of collaborator names
            exString = getExcitationGroupString(pictureFile[0]) # Given a file name, get the excitation in a nice html format
            text = html.H6([f'You\'re currently looking at the ', exString[0], exString[1], exString[2], ' of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames])
            image = os.path.join(picturePath,pictureFile[0])

    return levels, levels_title, image, text, isotopeLevels.to_json(orient='split')






# Run app...
if __name__ == '__main__':
    app.run(debug=True)
