import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly_express as px
import pickle
import pandas as pd
from rats.core.app import app
from rats.modules import bigpictureplots, scopeplots
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

placeholderfig = px.line(x=[1, 2, 3, 4], y=[1, 2, 3, 4],
                         title='placeholder')  # will be changed later, possibly to something representative

dropdownoptions = []
for i in range(12):
    item = {'label': f'Data Slot {i + 1}', 'value': i}
    dropdownoptions.append(item)


# this function could also be a callback now, which is fired on a button press...
def optionscreator(filenames):
    options = []
    for i in range(len(filenames)):
        if filenames[i] != 0:  # only append filename of inteterest, with index, no empty data!
            item = {'label': f'filename: {filenames[i]}', 'value': f'{filenames[i]}_ratdashfigures.pickle'}
            options.append(item)
    return options


# ======================================================================================================================
#       Creates placeholder html content to initialise the application (required; a quirk of Dash)
# ======================================================================================================================
def createcontent(numberofbanks):
    children = []
    options = []

    for i in range(numberofbanks):
        card = dcc.Loading([

            html.Div([
                html.Div([
                    html.P(['Select the file you want to interrogate in this bank of plots:']),
                    dcc.Dropdown(id=f'fileselect{i}',
                                 options=options, persistence=True, persistence_type='local'),
                    html.Br(),
                    html.Button(id=f'replot{i}', n_clicks=0, children='Plot Data', className='btn btn-secondary',
                                type='button'),
                    html.Br(),
                    html.P([], id=f'interscanprompt{i}', className='text-danger')
                ], className='card-header'),

                html.Div([
                    html.Div([
                        html.Div(id=f'bigpicture{i}', children=[
                            dcc.Graph(id=f'bigpictureplot{i}', figure=placeholderfig)
                        ], className='col-6 text-center'),

                        html.Div(id=f'scope{i}', children=[
                            dcc.Graph(id=f'scopeplot{i}', figure=placeholderfig),
                            dbc.Input(id=f"numberofscans{i}", type="number", value=10, persistence=True),
                            html.P('LLC buffer (data from +/- the number of LLC events here will be added to the plot)')
                        ], className='col-6 text-center'),

                    ], className='row')
                ], className='card-body')

            ], className='card', style={'height': 'auto'})])

        children.append(html.Br())
        children.append(card)

    return children


# ======================================================================================================================
#      Core functionality to handle plots in the ratdash app, called below by relevant callbacks
# ======================================================================================================================
def plotbank(replot, bigpictureclickdata, file, scans, bigpictureplot):
    if replot == 0:
        raise PreventUpdate

    try:
        # try to load figures from storage
        with open(str(packagepath) + figurepath + f'{file}_ratdashfigures.pickle', 'rb') as f:
            figs = pickle.load(f)
        print('plotbank loaded figures')

    except Exception:
        # if there are no figures in storage, make them and save them
        df = pd.read_feather(str(packagepath) + dfpath + f'{file}.feather')
        print(str(packagepath) + dfpath + f'{file}.feather')
        print(df.head())

        print(df.head())
        bp = bigpictureplots.bigpictureplot(df)
        s = scopeplots.scopeplot(df, buffer=scans)
        figs = dict(bigpictureplot=bp, scopeplot=s)
        print('plotbank created figures from scratch')

    # ========================================================
    # PLOT LINKAGES
    # ========================================================
    if bigpictureclickdata is not None:
        print('DATA SELECTED FROM BIGPICTURE:')
        print(f'bigpicture click data: {bigpictureclickdata}')
        # do relevant operations if we have clicked big picture
        # update scope plot here
        df = pd.read_feather(str(packagepath) + dfpath + f'{file}.feather')
        start = bigpictureclickdata['points'][0]['customdata'][0]
        print(f'start: {start}')
        scopeplot = scopeplots.scopeplot(df, llc=start, buffer=scans)
        figs['scopeplot'] = scopeplot
        # save out modifications

        with open(str(packagepath) + figurepath + f'{file}_ratdashfigures.pickle', 'wb') as f:
            pickle.dump(figs, f)

    else:
        with open(str(packagepath) + figurepath + f'{file}_ratdashfigures.pickle', 'wb') as f:
            pickle.dump(figs, f)

    return figs['bigpictureplot'], figs['scopeplot']


# ======================================================================================================================
#       Pull pre-processed data into ratdash app, update the data selection
# ======================================================================================================================
@app.callback([Output('fileselect0', 'options'),
               Output('fileselect1', 'options'),
               Output('pulldataratdash', 'children')],
              [Input('pulldataratdash', 'n_clicks')])
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
        return options, options, 'Data has been pulled into app'
    except Exception:
        return 'no file to display', 'no file to display'


# ======================================================================================================================
#       Handle layout and plotting in the first bank of plots
# ======================================================================================================================
@app.callback([Output('bigpictureplot0', 'figure'),
               Output('scopeplot0', 'figure')],
              [Input('replot0', 'n_clicks'),
               Input('bigpictureplot0', 'clickData')],
              [State('fileselect0', 'value'),
               State('numberofscans0', 'value'),
               State('bigpictureplot0', 'figure')])
def plotbank0(replot0, bigpictureclickdata0, file0, llcbuffer, bigpictureplot):
    return plotbank(replot0, bigpictureclickdata0, file0, llcbuffer, bigpictureplot)


# ======================================================================================================================
#       Handle layout and plotting in the second bank of plots
# ======================================================================================================================
@app.callback([Output('bigpictureplot1', 'figure'),
               Output('scopeplot1', 'figure')],
              [Input('replot1', 'n_clicks'),
               Input('bigpictureplot1', 'clickData')],
              [State('fileselect1', 'value'),
               State('numberofscans1', 'value'),
               State('bigpictureplot1', 'figure')])
def plotbank1(replot1, bigpictureclickdata1, file1, llcbuffer, bigpictureplot):
    return plotbank(replot1, bigpictureclickdata1, file1, llcbuffer, bigpictureplot)
