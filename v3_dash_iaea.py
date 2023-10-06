# This will likely need to be divided into other functions later. just getting things set up

# Handle data effectively
import pandas as pd
import numpy as np
import iaea_data as iaea # importing iaea data

import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from dash import Dash, dcc, html, Input, Output, State, callback
import dash_daq as daq
import json

# Custom dash functions
import nuclear_chart_views as ncv

# Call ground state information
ground_state = iaea.NuChartGS()
# print(ground_state)
# Call specific level scheme
# print(iaea.NuChartLevels(8,'C'))

def normalCol(dfCol):
    # Normalizes a give dataframe column
    return (dfCol - dfCol.min()) / (dfCol.max() - dfCol.min())
decayColor = {'B-':'skyblue','Stable':'black','N':'royalblue','2N':'blue','P':'deeppink','A':'yellow',
              'EC':'palevioletred','2P':'red','B+':'pink','2B-':'darkviolet','SF':'lime','Not Available':'grey'}

# Begin dash layout design
app = Dash(__name__)


########## View type / Chart Manipulation and Nuclear Chart Block ##########
plot_and_components = html.Div(
    children=[
        #### Options and View Type ####
        html.Div(
            children=[
                ##### View Type #####
                html.P('Please select your desired view:'),
                dcc.Dropdown(
                    ['Half Life', 'Main Decay Mode'],
                    'Half Life',
                    id='chart_type'
                ),
                ##### Proton Slider #####
                html.Label('Show Proton Range:'),
                dcc.Slider(
                    ground_state['z'].min(),
                    ground_state['z'].max(),
                    step=None,
                    id='proton_axis_slider',
                    value=ground_state['z'].max()
                ),
                ##### Neutron Slider #####
                html.Label('Show Proton Range:'),
                dcc.Slider(
                    ground_state['n'].min(),
                    ground_state['n'].max(),
                    step=None,
                    id='neutron_axis_slider',
                    value=ground_state['n'].max()
                ),
                ##### Extra Clickable Options #####
            ],
            style={'display': 'inline-block', 'vertical-align': 'top','width':'20%'}
        ),
        ########### Nuclear Chart ###########
        html.Div(
            children=[
                dcc.Graph(
                    # figure=chart,
                    id='nuclear_chart'
                    # clickData={'points':[{'customDataN':8},{'customDataSym':'O'}]}
                )
            ],
            style={'display': 'inline-block', 'width':'75%'}
        )
    ]
)

level_scheme_and_images = html.Div(
    children=[
        ########### Level Schemes ###########
        html.Div(
            children=[
                html.P(id='display_level_nucleus_name'),
                dcc.Graph(
                    id='level_scheme'
                    # clickData={'points':[{'customDataN':8},{'customDataSym':'O'}]}
                )
            ],
            style={'display': 'inline-block', 'width':'50%'}
        ),
        ########### Block Level Picture ###########
        # html.Div(
        #     children=[
        #         html.P(id='display_level_nucleus_name'),
        #         dcc.Graph(
        #             id='block_built_nucleus'
        #             # clickData={'points':[{'customDataN':8},{'customDataSym':'O'}]}
        #         )
        #     ],
        #     style={'display': 'inline-block', 'width':'50%'}
        # )
    ]
)


app.title = 'Welcome to the Interactive Nuclear Chart!'

# Begin describing the layout of the figure from top down...
app.layout = html.Div(
    children=[
        plot_and_components,
        level_scheme_and_images
    ]
)



# Plotting functions which will be used below
def plot_separation_energy(fig_,s_,nucType,nucColor):
    try: # When we don't have a separation energy, the conversion to float will throw an error
        s_ = float(s_)
        print('plotting S')
        full_fig = fig_.full_figure_for_development() # Gets information about the current figure in workable python form
        xAxisRange = full_fig.layout.xaxis.range
        fig_.add_trace(go.Scatter(
            x=xAxisRange, y=[float(s_),float(s_)],
            mode='lines',
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


# Now set any necessary callbacks corresponding to the ids given in the layout section
@callback(
    Output('nuclear_chart','figure'),
    Input('chart_type','value'),
    Input('neutron_axis_slider','value'),
    Input('proton_axis_slider','value')
)
def update_chart_type(chart_type_name,neutron_slider,proton_slider):
    currentData = ground_state.loc[(ground_state['n']<=neutron_slider)&(ground_state['z']<=proton_slider),:].copy()
    chart = go.Figure()

    if chart_type_name == 'Half Life':
        rows = currentData['z'].unique()
        cols = currentData['n'].unique()
        constructedMap = np.ones((len(rows),len(cols))) * np.nan
        dataNames = np.ones((len(rows),len(cols)),dtype=str)
        dataNames[:,:] = 'Nonexistent'
        dataDecay = np.ones((len(rows),len(cols)),dtype=str)
        dataDecay[:,:] = 'Nonexistent'

        stableNuclei = currentData[currentData['half_life']=='STABLE']
        for i, row in stableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = 1
            dataNames[row['z'],row['n']] = row['A_symbol']
            dataDecay[row['z'],row['n']] = row['common_decays']
        
        notAvailableNuclei = currentData[currentData['half_life']==' ']
        for i, row in notAvailableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = 0.5
            dataNames[row['z'],row['n']] = row['A_symbol']
            dataDecay[row['z'],row['n']] = row['common_decays']
        constructedMap[0,-1] = 0 # To set a zero point for our grey-scales

        stableMap = go.Heatmap(
            z=constructedMap.tolist(),
            colorscale='gray_r',
            name='',
            xgap=0.5, # Provide slight gap between each heatmap box
            ygap=0.5, # Provide slight gap between each heatmap box
            customdata=np.dstack((dataNames,dataDecay)),
            hovertemplate='%{customdata[0]}<br>' + # Uses data from dataNames argument above
                '%{x} Neutrons<br>' + # Uses data from dataNeutr argument above
                '%{y} Protons<br>' + # Uses data from dataProto argument above
                '%{customdata[1]} Decay Mode<br>', # Uses data from dataProto argument above
            showlegend=False,
            showscale=False
        )

        # Recreate the map
        constructedMap = np.ones((len(rows),len(cols))) * np.nan
        unstableNuclei = currentData[(currentData['half_life']!='STABLE')&(currentData['half_life']!=' ')]
        for i, row in unstableNuclei.iterrows():
            constructedMap[row['z'],row['n']] = row['log(half_life_sec)']
            dataNames[row['z'],row['n']] = row['A_symbol']
            dataDecay[row['z'],row['n']] = row['common_decays']
        
        unstableMap = go.Heatmap(
            z=constructedMap.tolist(),
            colorscale='jet',
            name='',
            xgap=0.5, # Provide slight gap between each heatmap box
            ygap=0.5, # Provide slight gap between each heatmap box
            customdata=np.dstack((dataNames,dataDecay)),
            hovertemplate='%{customdata[0]}<br>' + # Uses data from dataNames argument above
                '%{x} Neutrons<br>' + # Uses data from dataNeutr argument above
                '%{y} Protons<br>' + # Uses data from dataProto argument above
                '%{customdata[1]} Decay Mode<br>', # Uses data from dataProto argument above
            colorbar=dict(title='log<sub>10</sub>(T<sub>1/2</sub> (s))', # Update information on the colorbar
                        len=0.7,
                        tickvals=[-21,-9,0,9,21],
                        ticktext=['zs','ns','s','Gs (or 31.7 years)','Zs (or 31.7 trillion years)'])
        )

        chart.add_traces([unstableMap,stableMap])
    # ADD IF STATEMENTS FOR OTHER CHART TYPES HERE AND BE SURE TO INCLUDE IT IN THE DROPDOWN MENU IN THE LAYOUT ABOVE
    # elif chart_type_name == 'Main Decay Mode':
    chart.update_xaxes(title_text='Number of Neutrons',showspikes=True)
    chart.update_yaxes(title_text='Number of Protons',showspikes=True)
    chart.update_traces(customdata=[currentData['n'],currentData['symbol']]) # For click data info
    return chart
'''
Using squares. WARNING VERY SLOW!!!!!!!!!!!
def update_chart_type(chart_type_name,neutron_slider,proton_slider):
    currentData = ground_state.loc[(ground_state['n']<=neutron_slider)&(ground_state['z']<=proton_slider),:].copy()

    chart = go.Figure()
    chart.add_trace(go.Scatter(
        x=currentData['n'],
        y=currentData['z'],
        text=currentData['A_symbol'],
        name='', # Hides legend ID from showing on the side of hover info
        mode='none', # Eliminates any extra marker colors
        hovertemplate= # template for hover text
        '%{text}<br>' + # Uses data from 'text' argument above
        '%{x} Neutrons<br>' + # Uses data from 'x' argument above
        '%{y} Protons', # Uses data from 'y' argument above
        showlegend=False
    ))
    if chart_type_name == 'Half Life':
        # Make square colorscale
        color_scale = 'jet'
        currentData['normColor'] = normalCol(currentData['log(half_life_sec)'])
        interpolated_colors = [pc.sample_colorscale(color_scale,value)[0] for value in currentData['normColor']]
        print(len(interpolated_colors),len(currentData))
        for irow in range(len(currentData)):
            row = currentData.iloc[irow]
            xMid, yMid = row['n'], row['z']
            x0, x1 = xMid-0.5, xMid+0.5
            y0, y1 = yMid-0.5, yMid+0.5
            if irow % 20 == 0:
                print(irow)
            chart.add_shape(type='rect',
                          x0=x0,y0=y0,x1=x1,y1=y1,
                          line=dict(color=interpolated_colors[irow]),
                          fillcolor=interpolated_colors[irow])
        chart.update_xaxes(showspikes=True)
        chart.update_yaxes(showspikes=True)
    elif chart_type_name == 'Main Decay Mode':
        chart = px.scatter(currentData,x='n',y='z',color='common_decays',color_discrete_map=decayColor)
        chart.update_traces(marker_symbol='square')
    # chart.update_traces(customdata=[currentData['n'],currentData['symbol']]) # For click data info
    return chart
'''

#### Level chart ####
@callback(
    Output('level_scheme','figure'),
    Output('display_level_nucleus_name','children'),
    Input('nuclear_chart','clickData')
)
def update_level_scheme(nucData):
    dump = json.loads(json.dumps(nucData))
    
    levels = go.Figure()
    if dump is None:
        levels.add_trace(go.Scatter(
            x=[1],
            y=[1],
            text=["Please click a nucleus to see its levels"],
            mode="text",
        ))
        # Default header information 
        headerText = html.Td(['Level scheme for your selected nucleus: '])
    else:
        nucDataDict = dump['points'][0]
        print(nucDataDict)
        element = ground_state.loc[(ground_state['z']==nucDataDict['y'])] # Get element chain data
        isotope = element[element['n']==nucDataDict['x']] # Get specific isotope data
        symbol = isotope['symbol'].values[0] # Get corresponding symbol name for element
        
        # Get level data and plot levels
        levelScheme = iaea.NuChartLevels(nucDataDict['x']+nucDataDict['y'],symbol)
        levels.add_trace(go.Scatter(
            y=levelScheme['energy'],
            mode="markers",
            name='States'
        ))
        # levels = px.scatter(levelScheme,y='energy')

        # get header information for considered nucleus
        headerText = html.Td(['Level scheme for your selected nucleus: ',
                              html.Sup(str(nucDataDict['x']+nucDataDict['y'])), symbol])
        
        # Plot Separation energies
        sn = isotope['sn'].values[0] # Still in string format! Handle with function below...
        sp = isotope['sp'].values[0] # Still in string format! Handle with function below...
        print('Sp = ',sp)
        print('Sn = ',sn)
        plot_separation_energy(levels,sn,'Neutron','blue')
        plot_separation_energy(levels,sp,'Proton','red')
        levels.update_legends()

    return levels, headerText




# Run app...
if __name__ == '__main__':
    app.run(debug=True)