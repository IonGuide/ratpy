import dash_core_components as dcc
import dash_html_components as html
from rats.core.app import app
import rats.apps.ratdash as ratdash
import rats.apps.scopeapp as scopeapp
import rats.apps.interscanapp as interscanapp
import rats.callbackfunctions.corecallbacks as corecallbacks
import dash_uploader as du

topodatatable = corecallbacks.populatetoporeport()

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    #############################################################################################
    # HEADER
    #############################################################################################
    html.Div([
        html.H1(['RATS Data Processing']),

        html.Button(['Shutdown'], id='shutdown', n_clicks=None, className='btn btn-danger',
                    type='button'),
        html.Div([], id='runstatus', className='text-center text-danger'),
        html.Br(),

        # ==================================================
        # the du.Upload max_files attribute is still experimental. This is a potential weak point in the app
        # but seems to work fine for now
        # ==================================================

        du.Upload(max_files=10,
                  filetypes=['txt'],
                  text='Drag and drop here or click to browse',
                  text_completed='DONE! Click Here or Drag and Drop to Upload More Files. '
                                 'File(s) Uploaded Include:',
                  ),

        html.Br(),
        html.Div([html.Div([], id='errorlog', className='col')], id='errorlogcontainer',
                 className='container'),

        html.Div([html.Button(id='processdata', children='Pre-process the data',
                              className='btn btn-secondary', type='button')]),
    ], className='jumbotron text-center mx-auto'),

    dcc.Loading([
        html.Div(children=[html.Div([], id='datalist', className='col')],
                 id='datalistcontainer', className='container'),
    ]),

    html.Br(),

    html.Div([
        dcc.Textarea(
            id='notes',
            value='This is a space for any quick notes you may want to make.'
                  '\n Drag the bottom-right corner to expand',
            style={'width': '100%', 'height': 100},
            persistence=True,
            persistence_type='local'
        ),
    ], className='container'),

    html.Br(),

    #############################################################################################
    # BODY CONTENT
    #############################################################################################
    dcc.Tabs(id='rattab', persistence=True, persistence_type='local', children=[

        # ==========================================================================================
        #    Apps go here.. will load with loop eventually
        # ==========================================================================================
        dcc.Tab(label='Big Picture', value='ratdash', children=[
            ratdash.layout
        ]),

        dcc.Tab(label='Scope App', value='scopeapp', children=[
            scopeapp.layout
        ]),

        dcc.Tab(label='Interscan App', value='interscanapp', children=[
            interscanapp.layout
        ])

    ]),
    html.Div(id='page-content'),

    #############################################################################################
    # FOOTER
    #############################################################################################

    html.Br(),
    html.Br(),
    html.Div([
        html.Button(['Clear Program Data'], id='cleardata', n_clicks=None,
                    className='btn btn-danger', type='button'),
        html.Div(id='clearstatus', className='text-center text-danger'),

        dcc.Upload(
            id='upload-topo',
            children=html.Div([
                'Drag and Drop or ',
                html.A('Select Relevant Topo Files')
            ]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            },
            # Allow multiple files to be uploaded
            multiple=True
        ),

        html.P('Topo files and EDS files loaded:'),
        html.Div([
            html.Div([topodatatable], id='toporeport', className='col')
        ], id='topodatacontainer', className='col'),

        html.Br(),
        html.Button(['Clear Topo Data'], id='cleartopo', n_clicks=None,
                    className='btn btn-danger', type='button'),

        html.Div([], id='clearedtopo', className='col')

    ], className='jumbotron text-center mx-auto'),

])

app.run_server()
