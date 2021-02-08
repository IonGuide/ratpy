import dash_html_components as html
from rats.callbackfunctions import scopeappcallbacks
import dash_bootstrap_components as dbc

children = scopeappcallbacks.createcontent(3)

layout = html.Div([
                    ########################################
                    # dynamic plot content goes below, based on function output. Generic 3 entries for now - max 3 entries - one option could be subplots but lock to one entry
                    ########################################
                    html.Br(),
                    html.Div(
                        [html.Div(
                            [html.Div(
                                [html.Button(id='pulldatascope',children='Pull the data into Scope app',className='btn btn-secondary', type='button')
                                ],id='scopepullcontainer',className='col-12 text-center')
                            ], className='row')
                        ],className='container text-center'),

                    html.Br(),
                    #put llc alignment here... maybe with a button that's called update alignment or something
                    html.Div([
                        html.Div([
                            html.P(['LLC of interest:']),
                            dbc.Input(id=f"llc", type="number", value=10, persistence=True),
                        ],className='col-6'),

                        html.Div([
                            html.P(['Number of LLC intervals to buffer (+/-) the trace:']),
                            dbc.Input(id=f"buffer", type="number", value=10, persistence=True),
                        ], className='col-6'),

                    ],className='row'),

                    html.Br(),

                    html.Div(id='scoopeplots',children= children,
                    className='container-fluid text-center'),
                    ########################################
                    ], className='container-fluid')