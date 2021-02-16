import dash_html_components as html
from rats.callbackfunctions import ratdashcallbacks

children = ratdashcallbacks.createcontent(2)

layout = html.Div([
                    ########################################
                    # dynamic plot content goes below, based on function output. Generic 3 entries for now - max 3 entries - one option could be subplots but lock to one entry
                    ########################################
                    html.Br(),
                    html.Div(
                        [html.Div(
                            [html.Div(
                                [html.Button(id='pulldataratdash',children='Pull the data into Big Picture App',
                                             className='btn btn-secondary', type='button')
                                ],id='ratdashpullcontainer',className='col-12 text-center')
                            ], className='row')
                        ],className='container text-center'),


                    html.Div(id='plots',children= children,
                    className='container-fluid text-center'),
                    ########################################
                    ], className='container-fluid')









