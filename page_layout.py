# Handle data effectively
import pandas as pd
import numpy as np
import os

import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from dash import Dash, dcc, html, Input, Output, State, callback
from dash import ctx # Used for identifying callback_context
import dash_daq as daq
import dash_bootstrap_components as dbc
import json


# Iris bar figure
def drawFigure():
    xdat = np.arange(0,20)
    ydat = xdat**2
    df = pd.DataFrame({'x':xdat,'y':ydat})
    return  html.Div([
        dbc.Card(
            dbc.CardBody([
                dcc.Graph(
                    figure=px.scatter(
                        df, x="x", y="y"
                    ).update_layout(
                        template='plotly_dark',
                        plot_bgcolor= 'rgba(0, 0, 0, 0)',
                        paper_bgcolor= 'rgba(0, 0, 0, 0)',
                    ),
                ) 
            ])
        ),  
    ])

# Text field
def drawText():
    return html.Div([
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    html.H2("Text"),
                ], style={'textAlign': 'center'}) 
            ])
        ),
    ])


app = Dash(__name__,external_stylesheets=[dbc.themes.SLATE])

main_layout = html.Div([
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    drawText()
                ], width=3),
                dbc.Col([
                    drawFigure()
                ], width=9),
            ], align='center'), 
            html.Br(),
            dbc.Row([
                dbc.Col([
                    drawFigure()
                ], width=6),
                dbc.Col([
                    drawFigure()
                ], width=6),
            ], align='center'),      
        ]), color = 'dark'
    )
])

app.layout = main_layout

# Run app...
if __name__ == '__main__':
    app.run(debug=True)