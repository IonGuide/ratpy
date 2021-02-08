import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import pandas as pd
from dash.dependencies import Input,Output,State
from dash.exceptions import PreventUpdate
import plotly_express as px
import pickle
from rats.core.app import app
from rats.modules import scopeplots
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


#================================================================================================================================================
#       Creates placeholder content to feed into inital html in the application (required; a quirk of Dash)
#================================================================================================================================================
dropdownoptions = []
for i in range(12):
    item = {'label': f'Data Slot {i+1}', 'value': i}
    dropdownoptions.append(item)

placeholderfig = px.line(x=[1,2,3,4], y=[1,2,3,4], title='placeholder') #will be changed later, possibly to something representative

dropdownoptions = []
for i in range(12):
    item = {'label': f'Data Slot {i + 1}', 'value': i}
    dropdownoptions.append(item)

## this function could also be a callback now, which is fired on a button press...
def optionscreator(filenames):
    options = []
    for i in range(len(filenames)):
        if filenames[i] != 0:  # only append filename of inteterest, with index, no empty data!
            item = {'label': f'filename: {filenames[i]}', 'value': f'{filenames[i]}_figures.pickle'}
            options.append(item)
    return options



#================================================================================================================================================
#       Creates placeholder html content to initialise the application (required; a quirk of Dash)
#================================================================================================================================================
def createcontent(numberofbanks):
    children = []
    options = []

    cards = []
    for i in range(numberofbanks):

        card = html.Div([
                    html.Div([
                        html.P(['Select the file you want to interrogate in this bank of plots:']),
                        dcc.Dropdown(id=f'scopeappfileselect{i}',
                                     options=options, persistence=True),
                        html.Br(),
                        html.P(['Figure Height']),

                        dcc.Slider(id=f'scopeappheight{i}', min=500, max=2000, step=100, value=500,
                                    marks={x: str(x) for x in range(5,20,10)}),


                        html.Br(),
                        html.Button(id=f'scopeappreplot{i}', n_clicks=0, children='Plot Data', className='btn btn-secondary',
                                    type='button'),
                    ], className='card-header'),

                    html.Div([
                        dcc.Graph(id=f'scopeappplot{i}', figure=placeholderfig)],
                        className='card-body',id=f'scopeappplotcontainer{i}'),

                ],className='card')

        cards.append(card)

    group = html.Div(children=cards, className='card-group')

    return group


@app.callback([Output('scopeappfileselect0','options'),
               Output('scopeappfileselect1','options'),
               Output('scopeappfileselect2','options'),
               Output('pulldatascope','children')],
              [Input('pulldatascope','n_clicks')])
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

        return options,options,options,'Data has been pulled into app'
    except:
        return 'no file to display','no file to display'


#==============================================================================================================================
#       CORE CODE TO DEAL WITH FIGURE UPDATES AND SAVING
#==============================================================================================================================
def plotbank(replot,file,llc,buffer,height=500):
    if replot == 0:
        raise PreventUpdate

    # if there are no figures in storage, make them and save them
    df = pd.read_feather(str(packagepath) + dfpath + f'{file}.feather')
    s = scopeplots.scopeplot(df,llc=llc,buffer=buffer,facet=True)

    s.update_layout(height=height) #make this a variable on a slider??

    figs = dict(scopeplot=s)
    # dump figures into pickle for later use if necessary
    with open(str(packagepath) + figurepath + f'{file}_scopeappfigures.pickle', 'wb') as f:
        pickle.dump(figs, f)

    return figs['scopeplot']



#==============================================================================================================================
#               CALLBACKS
#==============================================================================================================================
@app.callback(Output('scopeappplot0','figure'),
              [Input('scopeappreplot0','n_clicks'),
               Input('llc','value'),
               Input('buffer','value')],
              [State('scopeappfileselect0','value'),
               State('scopeappheight0','value')])
def scopeappplotbank0(replot,llc,buffer,file,height):

    return plotbank(replot,file,llc,buffer,height)

@app.callback(Output('scopeappplot1','figure'),
              [Input('scopeappreplot1', 'n_clicks'),
               Input('llc','value'),
               Input('buffer','value')],
              [State('scopeappfileselect1', 'value'),
               State('scopeappheight1','value')])
def scopeappplotbank1(replot,llc,buffer,file,height):

    return plotbank(replot,file,llc,buffer,height)

@app.callback(Output('scopeappplot2','figure'),
              [Input('scopeappreplot2', 'n_clicks'),
               Input('llc','value'),
               Input('buffer','value')],
              [State('scopeappfileselect2', 'value'),
               State('scopeappheight2','value')])
def scopeappplotbank2(replot,llc,buffer,file,height):

    return plotbank(replot,file,llc,buffer,height)
