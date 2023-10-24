# This will likely need to be divided into other functions later. just getting things set up

# Handle data effectively
import pandas as pd
import numpy as np
import os
import iaea_data as iaea # importing iaea data

import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from dash import Dash, dcc, html, Input, Output, State, callback, no_update
from dash import ctx # Used for identifying callback_context
import dash_daq as daq
import dash_bootstrap_components as dbc
import json

# Custom dash functions
import nuclear_chart_views as ncv
import nuclear_chart_display_types as ncdt
import level_scheme_display_functions as lsdf

# Call ground state information
ground_state = iaea.NuChartGS()
currentData = None
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

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False



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
                    ['Half Life', 'Binding Energy Per Nucleon', 'Year Discovered'],
                    'Year Discovered',
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
        ),
        dbc.Card(
            [
                ##### Toggle Options #####
                dbc.Label('Toggle Options:'),
                dbc.Checklist(
                    options=[
                        {'label':'Show N=Z line','value':1}
                    ],
                    value=[],
                    id='chart_toggle_options',
                    switch=True
                    # value=ground_state['n'].max()
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
            id='nuclear_chart',style={'height':'80vh'},
            clear_on_unhover=True
        ),
        dcc.Tooltip(id='chart_tooltip')
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
    Input('proton_axis_slider','value'),
    Input('chart_toggle_options','value')
)
def update_chart_type(chart_type_name,neutron_slider,proton_slider,toggle_options):
    global currentData
    currentData = ground_state.loc[(ground_state['n']<=neutron_slider)&(ground_state['z']<=proton_slider),:]
    print('Current Data\n',currentData)
    xoffset, yoffset = 2, 2.5
    xrange = [min(currentData['n'])-xoffset, max(currentData['n'])]
    yrange = [min(currentData['z'])-yoffset, max(currentData['z'])]
    chart = go.Figure()

    if chart_type_name == 'Half Life':
        ncdt.show_user_made_nuclei(chart,currentData)
        chart_type, dataNames, dataDecay = ncdt.half_life_plot(currentData)
        chart.add_traces([chart_type])
        chart.update_layout(title=dict(text='Nuclear Chart: log(Half Life)'))
        
    elif chart_type_name == 'Binding Energy Per Nucleon':
        ncdt.show_user_made_nuclei(chart,currentData)
        chart_type, dataNames, dataDecay = ncdt.binding_energy_per_nucleon_plot(currentData)
        chart.add_traces([chart_type])
        chart.update_layout(title=dict(text='Nuclear Chart: Binding Energy Per Nucleon'))
    
    elif chart_type_name == 'Year Discovered':
        ncdt.show_user_made_nuclei(chart,currentData)
        chart_type, dataNames, dataDecay = ncdt.year_discovered_plot(currentData)
        chart.add_traces([chart_type])
        chart.update_layout(title=dict(text='Nuclear Chart: Year Discovered'))

    ncdt.drawMagicNumbers(chart,xrange,yrange,xoffset, yoffset)
    chart.update_layout(yaxis_scaleanchor='x') # Fix aspect ratio
    chart.update_xaxes(title_text='Number of Neutrons',showspikes=True,range=xrange,showgrid=False)
    chart.update_yaxes(title_text='Number of Protons',showspikes=True,range=yrange,automargin=True,showgrid=False)
    
    # Trace info allows showing default Plotly hover info. uncomment if you'd like default. otherwise see "display_hover" function
    '''
    chart.update_traces(customdata=np.dstack((dataNames,dataDecay)),
                        hovertemplate='%{customdata[0]}<br>' + # Uses data from dataNames argument above
                        '%{x} Neutrons<br>' + # Uses data from dataNeutr argument above
                        '%{y} Protons<br>' + # Uses data from dataProto argument above
                        '%{customdata[1]} Decay Mode<br>', # Uses data from dataProto argument above
                ) # For click data info
    Try more interactive plotly hover info
    '''
    chart.update_traces(hoverinfo='none',hovertemplate=None)
    
    # Toggle Options
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
    return chart

# Prettier hover info stuff for nuclear chart
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

    df_row = currentData[(currentData['n']==pt['x'])&(currentData['z']==pt['y'])]
    # For no data, Return nothing
    if df_row.empty:
        return False, no_update, no_update
    
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
    decayLatex = {
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
    img_src = decayImgSrc[str(df_row['common_decays'].values[0])]
    A =  int(df_row['n'].values[0])+int(df_row['z'].values[0])
    symbol = df_row['symbol'].values[0]
    text = [html.Sup(str(A)), symbol]

    children = [
        html.Div([
            html.H1(text),
            html.P(decayLatex[str(df_row['common_decays'].values[0])]),
            html.Img(src=img_src, style={"width": "100%"}),
            html.P(['Images are a general depiction of the decay process.'],style={'font-size':'12px'}),
        ], style={'width': '200px', 'white-space': 'normal'})
    ]

    return True, bbox, children


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

    # When we click on a new nucleus on the nuclear, load the corresponding level data
    if triggerID == 'nuclear_chart':
        nucDataDict = dump['points'][0]
        n, z = nucDataDict['x'], nucDataDict['y']
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
        text = ['Please select a nucleus to see a block version of it: ']
        image = imagePath + 'logo.png'
        builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,image)
        levels.update_layout(title=dict(text=f'Please select a nucleus:')) # Title
    elif triggerID == 'nuclear_chart':
        levels = lsdf.plot_level_scheme(ground_state,isotopeLevels)

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
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,image)
        else:
            discovererNames = collaboratorNames(pictureFile[0])
            text = ['You\'re currently looking at the excited  of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames]
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,os.path.join(picturePath,pictureFile[0]))
        
        levels.update_layout(title=dict(text=f'Level Scheme for <sup>{A}</sup>{symbol}')) # Title

    elif triggerID == 'level_scheme':
        levels = lsdf.plot_level_scheme(ground_state,isotopeLevels)

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
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,image)
        else:
            discovererNames = collaboratorNames(pictureFile[0])
            text = ['You\'re currently looking at the excited  of: ',
                    html.Sup(str(A)), symbol, html.Br(),
                    'Discovered by: ',discovererNames]
            builtNucleusHeader, builtNucleusPicture = lsdf.show_built_nucleus(text,os.path.join(picturePath,pictureFile[0]))
        
        levels.update_layout(title=dict(text=f'Level Scheme for <sup>{A}</sup>{symbol}')) # Title
    
    # return levels, headerText, builtNucleusHeader, builtNucleusPicture
    return levels, builtNucleusHeader, builtNucleusPicture






# Run app...
if __name__ == '__main__':
    app.run(debug=True)