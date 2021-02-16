import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly_express as px
import pickle
from rats.core.app import app
from rats.modules import interscanplots
import pathlib
import platform

if platform.system() == 'Windows':
    cachepath = '\\cache\\'
    dfpath = '\\feathereddataframes\\'
    figurepath = '\\pickledfigures\\'
else:
    cachepath = '/cache/'
    dfpath = '/feathereddataframes/'
    figurepath = '/pickledfigures/'

packagepath = pathlib.Path(__file__).parent.parent.resolve()

# ======================================================================================================================
#       Creates placeholder content to feed into inital html in the application (required; a quirk of Dash)
# ======================================================================================================================
dropdownoptions = []
for i in range(12):
    item = {'label': f'Data Slot {i + 1}', 'value': i}
    dropdownoptions.append(item)

dropdownoptions = []
for i in range(12):
    item = {'label': f'Data Slot {i + 1}', 'value': i}
    dropdownoptions.append(item)


# this function could also be a callback now, which is fired on a button press...
def optionscreator(filenames):
    options = []
    for i in range(len(filenames)):
        if filenames[i] != 0:  # only append filename of inteterest, with index, no empty data!
            item = {'label': f'filename: {filenames[i]}', 'value': f'{filenames[i]}_figures.pickle'}
            options.append(item)
    return options


# ======================================================================================================================
#       Creates placeholder html content to initialise the application (required; a quirk of Dash)
# ======================================================================================================================
def createcontent(numberofbanks):
    options = []

    cards = []
    for i in range(numberofbanks):
        card = html.Div([
            html.Div([
                html.P(['Select the file you want to interrogate in this bank of plots:']),
                dcc.Dropdown(id=f'interscanappfileselect{i}',
                             options=options, persistence=True),

                html.Br(),

                html.P(['Figure Height']),

                dcc.Slider(id=f'interscanappheight{i}', min=500, max=2000, step=100, value=500,
                           marks={x: str(x) for x in range(5, 20, 10)}),

                html.Br(),
                html.Button(id=f'interscanappreplot{i}', n_clicks=0, children='Plot Data',
                            className='btn btn-secondary',
                            type='button'),
            ], className='card-header'),

            html.Div([
                dcc.Graph(id=f'interscanappplot{i}', figure=[])],
                className='card-body', id=f'interscanappplotcontainer{i}'),

        ], className='card')

        cards.append(card)

    group = html.Div(children=cards, className='card-group')

    return group


@app.callback([Output('interscanappfileselect0', 'options'),
               Output('interscanappfileselect1', 'options'),
               Output('interscanappfileselect2', 'options'),
               Output('pulldatainterscan', 'children')],
              [Input('pulldatainterscan', 'n_clicks')])
def pulldata(click):
    if click is None:
        raise PreventUpdate

    options = []
    try:
        sessionfilenames = pd.read_feather(str(packagepath) + cachepath + 'sessionfilenames')

        filenames = sessionfilenames['file'].tolist()
        for i in range(len(filenames)):
            if filenames[i] != 0:  # only append filename of inteterest, with index, no empty data!
                item = {'label': f'filename: {filenames[i]}', 'value': f'{filenames[i]}'}
                options.append(item)

        return options, options, options, 'Data has been pulled into app'
    except Exception:
        return 'no file to display', 'no file to display'


# ======================================================================================================================
#       CORE CODE TO DEAL WITH FIGURE UPDATES AND SAVING
# ======================================================================================================================
def plotbank(replot, file, height=500):
    if replot == 0:
        raise PreventUpdate

    df = pd.read_feather(str(packagepath) + dfpath + f'{file}.feather')
    plot = interscanplots.interscanplot(df)

    plot.update_layout(height=height)

    return plot


# ======================================================================================================================
#               CALLBACKS
# ======================================================================================================================
@app.callback(Output('interscanappplot0', 'figure'),
              [Input('interscanappreplot0', 'n_clicks'),
               Input('interscanappfileselect0', 'value')],
              [State('interscanappheight0', 'value')])
def interscanappplotbank0(replot, file, height):
    return plotbank(replot, file, height)


@app.callback(Output('interscanappplot1', 'figure'),
              [Input('interscanappreplot1', 'n_clicks'),
               Input('interscanappfileselect1', 'value')],
              [State('interscanappheight1', 'value')])
def interscanappplotbank1(replot, file, height):
    return plotbank(replot, file, height)


@app.callback(Output('interscanappplot2', 'figure'),
              [Input('interscanappreplot2', 'n_clicks'),
               Input('interscanappfileselect2', 'value')],
              [State('interscanappheight2', 'value')])
def interscanappplotbank2(replot, file, height):
    return plotbank(replot, file, height)
