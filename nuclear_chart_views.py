# General layout forms for our nuclear chart

import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback
import dash_daq as daq

def default_chart_view():

    return html.Div(
        id='default-chart-container',
        children=[
            html.Div(
                ##### Chart Options #####
                id='chart-options',
                children=[
                    ##### Chart Type #####
                    html.Div(
                        id='chart-type',
                        children=[
                            html.P('Please select your desired view:'),
                            dcc.Dropdown(
                                ['Half Life', 'Main Decay Mode'],
                                'Half Life',
                                id='chart_type'
                            )
                        ]
                    ),
                    ##### Chart Manipulation (Proton&Neutron Sliders, etc.) #####
                    html.Div(children=[
                        ##### Proton Slider #####
                        html.Label('Show Proton Range:'),
                        dcc.Slider(
                            # ground_state['z'].min(),
                            # ground_state['z'].max(),
                            step=None,
                            id='proton_axis_slider'#,
                            # value=ground_state['z'].max()
                        ),
                        ##### Neutron Slider #####
                        html.Label('Show Proton Range:'),
                        dcc.Slider(
                            # ground_state['n'].min(),
                            # ground_state['n'].max(),
                            step=None,
                            id='neutron_axis_slider'#,
                            # value=ground_state['n'].max()
                        )
                    ])
                ],style={'display': 'inline-block', 'vertical-align': 'top','width':'20%','margin-left': '1vw'}
            ),
            ########### Nuclear Chart ###########
            html.Div(children=[
                    dcc.Graph(
                        figure=chart,id='nuclear_chart',
                        clickData={'points':[{'customDataN':8},{'customDataSym':'O'}]}
                    )
                ],style={'padding':'1rem', 'boxShadow': '#e3e3e3 4px 4px 2px', 'border-radius': '5px','width':'60%'}
            )
        ]
    )